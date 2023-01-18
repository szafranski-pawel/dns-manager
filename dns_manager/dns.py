from collections import defaultdict
from enum import Enum
import functools
import os
from typing import List, Optional
from flask import Blueprint, jsonify
from flask_login import login_required
from pydantic import BaseModel
from flask_pydantic import validate
import dns
import dns.resolver
import dns.tsigkeyring
import dns.update
import dns.zone
from .models import node_role
from .auth import roles_required
from .helpers import logger


# Allowed record types
class RecordType(str, Enum): #this is needed for pydantic to check if value is one of this
    a = 'A'
    aaaa = 'AAAA'
    cname = 'CNAME'
    mx = 'MX'
    ns = 'NS'
    txt = 'TXT'
    soa = 'SOA'
    ptr = 'PTR'
    iot = 'IOT'
    tlsa = 'TLSA'


class Record(BaseModel):
    record_type: RecordType
    record_value: str
    ttl: Optional[int] = 3600


class RecordsSet(BaseModel):
    before: Record
    after: Record


class QueryList(BaseModel):
    record_type: List[str]


# Global variables for dns funcs
DNS_SERVER = os.environ['BIND_SERVER']
TSIG = dns.tsigkeyring.from_text({os.environ['TSIG_USERNAME']: os.environ['TSIG_PASSWORD']})
VALID_ZONE = os.environ['BIND_ALLOWED_ZONES']

# Define blueprint
dns_bp = Blueprint('dns_bp', __name__, url_prefix='/api/dns')

# Some wrappers
resolver = dns.resolver.Resolver()
resolver.nameservers = [DNS_SERVER]
tcpquery = functools.partial(dns.query.tcp, where=DNS_SERVER)
def qualify(s): return f'{s}.' if not s.endswith('.') else s


# api request handlers
@dns_bp.route("/record/<domain>", methods=['GET'])
@login_required
@validate()
def get_record(domain: str, query: QueryList):
    domain = qualify(domain)

    if not domain.endswith(VALID_ZONE):
        return "", 400

    records = {}
    for record_type in query.record_type:
        try:
            answers = resolver.resolve(domain, record_type)
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            continue
        except Exception:
            return "", 400
        records[record_type] = [str(x) for x in answers.rrset]

    return jsonify(records), 200


@dns_bp.route("/all_records/<domain>", methods=['GET'])
@login_required
def get_all_records(domain: str):
    domain = qualify(domain)

    if not domain.endswith(VALID_ZONE):
        return "", 400

    records = {}
    for record_type in dns.rdatatype.RdataType:
        try:
            answers = resolver.resolve(domain, record_type)
            records[record_type.name] = [str(x) for x in answers.rrset]
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.DNSException):
            continue
        except Exception:
            return "", 400

    return jsonify(records), 200


@dns_bp.route("/zone/<zone>", methods=['GET'])
@login_required
@validate()
def get_zone(zone: str):
    zone = qualify(zone)

    if not zone.endswith(VALID_ZONE):
        return "", 400

    zone = dns.zone.from_xfr(dns.query.xfr(DNS_SERVER, zone))

    result = {}
    records = defaultdict(list)
    for (name, ttl, rdata) in zone.iterate_rdatas():
        if type(rdata.rdtype) != int:
            if rdata.rdtype.name == 'SOA':
                result['SOA'] = {
                    'ttl': ttl,
                }
                for n in ('expire', 'minimum', 'refresh', 'retry', 'rname', 'mname', 'serial'):
                    if n in ('rname', 'mname'):
                        result['SOA'][n] = str(getattr(rdata, n))
                    else:
                        result['SOA'][n] = getattr(rdata, n)
            else:
                records[str(name)].append({
                    'response': str(rdata),
                    'rrtype': rdata.rdtype.name,
                    'ttl': ttl,
                })
    result['records'] = records

    return jsonify(result), 200


def update_action():  # helper function
    return dns.update.Update(VALID_ZONE, keyring=TSIG) # this is always the base


# Methods for modifying records
@dns_bp.route("/record/<domain>", methods=['POST'])
@login_required
@roles_required(node_role)
@validate()
def create_record(domain: str, body: Record):
    logger.info("Record created")
    action = update_action()
    action.add(dns.name.from_text(domain), body.ttl, body.record_type, body.record_value)

    try:
        tcpquery(action)
    except Exception as e:
        return "", 400

    return "", 201


@dns_bp.route("/record/<domain>", methods=['DELETE'])
@login_required
@roles_required(node_role)
@validate()
def delete_record(domain: str, body: Record):
    logger.info("Record deleted")
    action = update_action()
    action.delete(dns.name.from_text(domain),body.record_type, body.record_value)

    try:
        tcpquery(action)
    except Exception:
        return "", 400

    return "", 200


@dns_bp.route("/record/<domain>", methods=['PUT'])
@login_required
@roles_required(node_role)
@validate()
def modify_record(domain: str, body: RecordsSet):
    logger.info("Record modify")
    action = update_action()
    print(body)
    action.delete(dns.name.from_text(domain), body.before.record_type, body.before.record_value)
    action.add(dns.name.from_text(domain), body.after.ttl, body.after.record_type, body.after.record_value)

    try:
        tcpquery(action)
    except Exception:
        return "", 400

    return jsonify(body.after.dict()), 200

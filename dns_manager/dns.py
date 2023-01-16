import functools
import os
from flask import Blueprint, request, jsonify
from flask_login import login_required
from pydantic import BaseModel, Field
from flask_pydantic import validate
import dns.resolver
import dns.tsigkeyring
import dns.update
from .models import node_role
from .auth import roles_required

dns_bp = Blueprint('dns_bp', __name__, url_prefix='/api/dns')

# Allowed record types
class RecordType(str):
    a = 'A'
    aaaa = 'AAAA'
    cname = 'CNAME'
    mx = 'MX'
    ns = 'NS'
    txt = 'TXT'
    soa = 'SOA'
    ptr = 'PTR'
    iot = 'IOT'

# Record
class Record(BaseModel):
    record_type: RecordType
    record_value: str = Field(..., example='1.1.1.1')
    ttl: int = Field(3600, example=3600)


# def normalize_query_param(value):
#     """
#     Given a non-flattened query parameter value,
#     and if the value is a list only containing 1 item,
#     then the value is flattened.

#     :param value: a value from a query parameter
#     :return: a normalized query parameter value
#     """
#     return value if len(value) > 1 else value[0]


# def normalize_query(params):
#     """
#     Converts query parameters from only containing one value for each parameter,
#     to include parameters with multiple values as lists.

#     :param params: a flask query parameters data structure
#     :return: a dict of normalized query parameters
#     """
#     params_non_flat = params.to_dict(flat=False)
#     return {k: normalize_query_param(v) for k, v in params_non_flat.items()}


DNS_SERVER = os.environ['BIND_SERVER']
TSIG = dns.tsigkeyring.from_text({os.environ['TSIG_USERNAME']: os.environ['TSIG_PASSWORD']})
VALID_ZONE = os.environ['BIND_ALLOWED_ZONES']

# Some wrappers
resolver = dns.resolver.Resolver()
resolver.nameservers = [DNS_SERVER]
tcpquery = functools.partial(dns.query.tcp, where=DNS_SERVER)
qualify = lambda s: f'{s}.' if not s.endswith('.') else s

@dns_bp.route("/record/<domain>", methods=['GET'])
@login_required
@roles_required(node_role)
def get_record(domain):
    domain = qualify(domain)
    query_params = request.args.to_dict(flat=False)
    print(domain)
    print(query_params)

    if not domain.endswith(VALID_ZONE) or 'record_type' not in query_params:
        return "", 400
    
    records = {}
    for record_type in query_params['record_type']:
        try:
            answers = resolver.resolve(domain, record_type)
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            continue
        records[record_type] = [str(x) for x in answers.rrset]
    
    return jsonify(records), 200


@dns_bp.route("/record/<domain>", methods=['POST'])
@login_required
@roles_required(node_role)
@validate()
def create_record(domain: str, body: Record):
    action = dns.update.Update(VALID_ZONE, keyring=TSIG)
    action.add(dns.name.from_text(domain), body.ttl, body.record_type, body.record_value)

    try:
        tcpquery(action)
    except Exception as e:
        print(e)
        return "", 400
    
    return "", 200

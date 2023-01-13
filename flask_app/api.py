from flask import Blueprint
from flask_login import login_required
import dns.resolver

api_bp = Blueprint('api_bp', __name__, url_prefix = '/api')

@api_bp.route("/get_all/<URL>", methods=['GET'])
@login_required
def get_all(URL):
    output = {}
    answers = dns.resolver.resolve(URL, 'A')
    for it, rdata in enumerate(answers):
        output[it] = str(rdata)
    return output


import json
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from .models import IotNode, db, user_role
from .auth import roles_required

api_bp = Blueprint('api_bp', __name__, url_prefix = '/api')

@api_bp.route("/node", methods=['GET'])
@login_required
@roles_required(user_role)
def get_iot():
    rows = IotNode.query.filter_by(user_id=current_user.id).all()
    return jsonify(rows), 200

@api_bp.route("/node", methods=['POST'])
@login_required
@roles_required(user_role)
def register_iot():
    new_iot_params = json.loads(request.data)
    if 'subdomain' in new_iot_params and '.' not in new_iot_params['subdomain']:
        iot_user = IotNode(
            user_id=current_user.id,
            domain=new_iot_params['subdomain']
        )
        iot_user.generate_api_key()
        db.session.add(iot_user)
        db.session.commit()  # Create new iot_user
        return iot_user.api_key, 201
    elif '.' in new_iot_params['subdomain']:
        return "", 400
    else:
        return "", 400


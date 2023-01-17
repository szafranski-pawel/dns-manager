import json
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from .models import UserNode, db, user_role
from .auth import roles_required
from flask_pydantic import validate
from pydantic import BaseModel, validator


class NodeBody(BaseModel):
    subdomain: str

    @validator('subdomain')
    def subdomain_cannnot_contain_dot(cls, v):
        if '.' in v:
            raise ValueError('domain name cannot contain dot')
        return v


api_bp = Blueprint('api_bp', __name__, url_prefix = '/api')


@api_bp.route("/node", methods=['GET'])
@login_required
@roles_required(user_role)
def get_node():
    rows = UserNode.query.filter_by(user_id=current_user.id).all()
    return jsonify(rows), 200


@api_bp.route("/node/<id>", methods=['GET'])
@login_required
@roles_required(user_role)
@validate()
def get_single_node(id: str):
    rows = UserNode.query.filter((UserNode.user_id==current_user.id) | (UserNode.id==id)).first()
    return jsonify(rows), 200


@api_bp.route("/node", methods=['POST'])
@login_required
@roles_required(user_role)
@validate()
def register_node(body: NodeBody):
    if not UserNode.query.filter_by(domain=body.subdomain).first():
        iot_user = UserNode(
            user_id=current_user.id,
            domain=body.subdomain
        )
        iot_user.generate_api_key()
        db.session.add(iot_user)
        db.session.commit()
        return iot_user.api_key, 201
    else:
        return "", 400


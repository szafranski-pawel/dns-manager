import json
from typing import Optional
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from .models import UserNode, db, user_role, admin_role, node_role, User
from .auth import roles_required
from flask_pydantic import validate
from pydantic import BaseModel, validator, EmailStr, SecretStr


class NodeBodyPost(BaseModel):
    subdomain: str

    @validator('subdomain')
    def subdomain_cannnot_contain_dot(cls, v):
        if '.' in v:
            raise ValueError('domain name cannot contain dot')
        return v

class NodeBodyPut(BaseModel):
    subdomain: Optional[str] = ""
    api_key: Optional[bool] = False

    @validator('subdomain')
    def subdomain_cannnot_contain_dot(cls, v):
        if '.' in v:
            raise ValueError('domain name cannot contain dot')
        return v


class UserBody(BaseModel):
    name: Optional[str] = ""
    email: Optional[EmailStr] = ""
    password: Optional[SecretStr] = ""
    subdomain: Optional[str] = ""
    api_key: Optional[bool] = False

    @validator('subdomain')
    def subdomain_cannnot_contain_dot(cls, v):
        if v and '.' in v:
            raise ValueError('domain name cannot contain dot')
        return v

    @validator('password')
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('password must be at least 8 chars')
        return v


api_bp = Blueprint('api_bp', __name__, url_prefix = '/api')


@api_bp.route("/user", methods=['GET'])
@login_required
@roles_required(admin_role)
def get_users():
    users = User.query.all()
    return jsonify(users), 200


@api_bp.route("/user/<id>", methods=['GET'])
@login_required
@roles_required(admin_role)
@validate()
def get_user(id: str):
    user = User.query.filter_by(id=id).first()
    if user:
        return jsonify(user), 200
    return "", 404


@api_bp.route("/user/<id>", methods=['DELETE'])
@login_required
@roles_required(admin_role)
@validate()
def delete_user(id: str):
    user = User.query.filter_by(id=id).first()
    if not user:
        return "", 404
    db.session.delete(user)
    db.session.commit()
    return "", 200

@api_bp.route("/user/<id>", methods=['PUT'])
@login_required
@roles_required(admin_role)
@validate()
def modify_user(id: str, body: UserBody):
    user = User.query.filter_by(id=id).first()
    if not user:
        return "", 404
    for key, val in body.dict().items():
        if not val or key in ['password', 'api_key']:
            continue
        setattr(user, key, val)
    if body.password:
        user.set_password(body.password.get_secret_value())
    if body.api_key:
        user.generate_api_key()
    try:
        db.session.commit()
    except Exception:
        return "", 400
    return jsonify(user), 200


@api_bp.route("/my_user", methods=['GET'])
@login_required
@roles_required(user_role)
@validate()
def get_my_user():
    return get_user.__wrapped__.__wrapped__(id=current_user.id)


@api_bp.route("/my_user", methods=['DELETE'])
@login_required
@roles_required(user_role)
@validate()
def delete_my_user():
    return delete_user.__wrapped__.__wrapped__(id=current_user.id)


@api_bp.route("/my_user", methods=['PUT'])
@login_required
@roles_required(user_role)
@validate()
def modify_my_user(body: UserBody):
    return modify_user.__wrapped__.__wrapped__(id=current_user.id, body=body)


@api_bp.route("/node", methods=['GET'])
@login_required
@roles_required(user_role)
def get_nodes():
    if admin_role in current_user.roles_list:
        nodes = UserNode.query.all()
    else:
        nodes = UserNode.query.filter_by(user_id=current_user.id).all()
    return jsonify(nodes), 200


@api_bp.route("/node", methods=['POST'])
@login_required
@roles_required(user_role)
@validate()
def register_node(body: NodeBodyPost):
    if admin_role not in current_user.roles_list and not UserNode.query.filter((UserNode.domain==body.subdomain) & (UserNode.user_id==current_user.id)).first():
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


@api_bp.route("/node/<id>", methods=['GET'])
@login_required
@roles_required(user_role)
@validate()
def get_node(id: str):
    if admin_role in current_user.roles_list or node_role in current_user.roles_list: # last condition for calls from /my_node
        node = UserNode.query.filter(UserNode.id==id).first()
    else:
        node = UserNode.query.filter((UserNode.user_id==current_user.id) & (UserNode.id==id)).first()
    if not node:
        return "", 404
    return jsonify(node), 200


@api_bp.route("/node/<id>", methods=['DELETE'])
@login_required
@roles_required(user_role)
@validate()
def delete_node(id: str):
    if admin_role in current_user.roles_list or node_role in current_user.roles_list: # last condition for calls from /my_node
        node = UserNode.query.filter(UserNode.id==id).first()
    else:
        node = UserNode.query.filter((UserNode.user_id==current_user.id) & (UserNode.id==id)).first()
    if not node:
        return "", 404
    db.session.delete(node)
    db.session.commit()
    return "", 200


@api_bp.route("/node/<id>", methods=['PUT'])
@login_required
@roles_required(user_role)
@validate()
def modify_node(id: str, body: NodeBodyPut):
    if admin_role in current_user.roles_list or node_role in current_user.roles_list: # last condition for calls from /my_node
        node = UserNode.query.filter(UserNode.id==id).first()
    else:
        node = UserNode.query.filter((UserNode.user_id==current_user.id) & (UserNode.id==id)).first()
    if not node:
        return "", 404
    if body.subdomain and not UserNode.query.filter((UserNode.domain==body.subdomain) & (UserNode.user_id==current_user.id)).first():
        setattr(node, 'domain', body.subdomain)
    elif UserNode.query.filter((UserNode.domain==body.subdomain) & (UserNode.user_id==current_user.id)).first():
        return "", 400
    if body.api_key:
        node.generate_api_key()
    try:
        db.session.commit()
    except Exception:
        return "", 400
    return jsonify(node), 200


@api_bp.route("/my_node", methods=['GET'])
@login_required
@roles_required(node_role)
@validate()
def get_my_node():
    return get_node.__wrapped__.__wrapped__(id=current_user.id)


@api_bp.route("/my_node", methods=['DELETE'])
@login_required
@roles_required(node_role)
@validate()
def delete_my_node():
    return delete_node.__wrapped__.__wrapped__(id=current_user.id)


@api_bp.route("/my_node", methods=['PUT'])
@login_required
@roles_required(node_role)
@validate()
def modify_my_node(body: NodeBodyPut):
    return modify_node.__wrapped__.__wrapped__(id=current_user.id, body=body)

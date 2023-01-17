from functools import wraps
import os
import uuid
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
import secrets
from dataclasses import dataclass

from . import db

node_role = 'Node'
user_role = 'User'
admin_role = 'Admin'

@dataclass
class User(UserMixin, db.Model):
    id: int
    name: str
    email: str
    domain: str
    api_key: str
    iot_users: "UserNode"

    roles_list = [node_role, user_role]

    id = db.Column(
        db.String,
        default = lambda: str(uuid.uuid4()),
        primary_key=True
    )
    name = db.Column(
        db.String(100),
        nullable=False,
        unique=False
    )
    email = db.Column(
        db.String(64),
        unique=True,
        nullable=False
    )
    password = db.Column(
        db.String(200),
        primary_key=False,
        unique=False,
        nullable=False
    )
    domain = db.Column(
        db.String(64),
        unique=True,
        nullable=False
    )
    api_key = db.Column(
        db.String(200),
        unique=True,
        nullable=False
    )
    iot_users = db.relationship("UserNode")

    def set_password(self, password):
        self.password = generate_password_hash(password, "pbkdf2:sha3_512:500000")

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def generate_api_key(self):
        self.api_key = secrets.token_hex(32)

    def has_roles(self, requirements):
        for req in requirements:
            if req not in self.roles_list:
                return False
        return True


@dataclass
class UserNode(UserMixin, db.Model):
    id: int
    # user_id: id
    domain: str
    api_key: str

    roles_list = [node_role]

    id = db.Column(
        db.String,
        default = lambda: str(uuid.uuid4()),
        primary_key=True
    )
    user_id = db.Column(
        db.String,
        db.ForeignKey(User.id)
    )
    domain = db.Column(
        db.String(64),
        unique=True,
        nullable=False
    )
    api_key = db.Column(
        db.String(200),
        unique=True,
        nullable=False
    )

    def generate_api_key(self):
        self.api_key = secrets.token_hex(32)

    def has_roles(self, requirements):
        for req in requirements:
            if req not in self.roles_list:
                return False
        return True


@dataclass
class Admin(UserMixin):
    api_key: str

    roles_list = [admin_role] + User.roles_list

    api_key = os.environ['BIND_ALLOWED_ZONES']

    def has_roles(self, requirements):
        for req in requirements:
            if req not in self.roles_list:
                return False
        return True
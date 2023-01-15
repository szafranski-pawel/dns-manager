from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
import secrets
from dataclasses import dataclass

from . import db
@dataclass
class User(UserMixin, db.Model):
	id: int
	name: str
	email: str
	domain: str
	api_key: str
	iot_users: "IotUser"

	id = db.Column(
		db.Integer,
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
	iot_users = db.relationship("IotUser")

	def set_password(self, password):
		self.password = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password, password)

	def generate_api_key(self):
		self.api_key = secrets.token_hex(32)

@dataclass
class IotUser(db.Model):
	id: int
	# user_id: id
	domain: str
	api_key: str

	id = db.Column(
		db.Integer,
		primary_key=True
	)
	user_id = db.Column(
		db.Integer,
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
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
import secrets

from . import db

class User(UserMixin, db.Model):
	"""User account model."""
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
	master_api_key = db.Column(
		db.String(200),
		primary_key=False,
		unique=True,
		nullable=False
	)

	def set_password(self, password):
		"""Create hashed password."""
		self.password = generate_password_hash(password)

	def check_password(self, password):
		"""Check hashed password."""
		return check_password_hash(self.password, password)

	def generate_api_key(self):
		self.master_api_key = secrets.token_hex(32)

	# def __repr__(self):
	# 	return 'User {}, API_KEY {}'.format(self.name, self.master_api_key)

from werkzeug.security import generate_password_hash, check_password_hash

from clapperboard.models import db
from clapperboard.models.common.utils import ClapQuery


class User(db.Model):
    query_class = ClapQuery

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column('password', db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.hash_password(password)

    def __repr__(self):
        return '<User %r>' % self.id

    def hash_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

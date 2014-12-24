from functools import wraps

from itsdangerous import URLSafeTimedSerializer

from flask import current_app

from flask.ext.restful import abort
from flask.ext.jwt import current_user


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.id != 1:
            abort(401)
        return f(*args, **kwargs)
    return decorated


def get_serializer():
    return URLSafeTimedSerializer(
        secret_key=current_app.config['EMAIL_V10N_SECRET_KEY'],
        salt=current_app.config['EMAIL_V10N_SALT']
    )

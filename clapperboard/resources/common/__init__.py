from functools import wraps

from flask.ext.restful import abort
from flask.ext.jwt import current_user


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.id != 1:
            abort(401)
        return f(*args, **kwargs)
    return decorated

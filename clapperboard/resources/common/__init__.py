from functools import wraps

from flask.ext.restful import marshal, marshal_with
from flask.ext.restful.utils import unpack


class marshal_with_key(marshal_with):
    def __init__(self, fields, key=None):
        self.key = key
        super(marshal_with_key, self).__init__(fields)

    def __call__(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            resp = f(*args, **kwargs)
            if isinstance(resp, tuple):
                data, code, headers = unpack(resp)
                marshaled = ({self.key: marshal(data, self.fields)}
                             if self.key else marshal(data, self.fields))
                return marshaled, code, headers
            else:
                marshaled = ({self.key: marshal(resp, self.fields)}
                             if self.key else marshal(resp, self.fields))
                return marshaled
        return wrapper

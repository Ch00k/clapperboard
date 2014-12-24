from flask.ext.restful import Resource, abort

from flask.ext.jwt import current_user

from webargs import Arg
from webargs.flaskparser import use_args

from clapperboard.resources.common.schemas import UserSchema

from clapperboard.resources.common.errors import (
    USER_NOT_FOUND,
    USER_NAME_EXISTS,
    USER_EMAIL_EXISTS
)

from clapperboard.resources.common.arg_validators import (
    user_create_json_validator,
    user_edit_json_validator
)

from clapperboard.models import db
from clapperboard.models.user import User


user_create_json = {
    'user': Arg(
        dict, target='json', required=True, validate=user_create_json_validator
    )
}


user_edit_json = {
    'user': Arg(
        dict, target='json', required=False, validate=user_edit_json_validator
    )
}


class UserListAPI(Resource):
    def __init__(self):
        super(UserListAPI, self).__init__()
        self.user_schema = UserSchema(exclude=('password',))

    @use_args(user_create_json)
    def post(self, args):
        email = args['user'].get('email')
        if User.query.filter_by(username=args['user']['username']).first():
            abort(400, status='error', code=400, message=USER_NAME_EXISTS)
        if email and User.query.filter_by(email=email).first():
            abort(400, status='error', code=400, message=USER_EMAIL_EXISTS)
        user = User(
            username=args['user']['username'],
            email=email,
            password=args['user']['password']
        )
        db.session.add(user)
        db.session.commit()
        res = self.user_schema.dump(user)
        return res.data


class UserAPI(Resource):
    def __init__(self):
        super(UserAPI, self).__init__()
        self.user_schema = UserSchema(exclude=('password',))

    @use_args(user_edit_json)
    def put(self, args, user_id):
        if current_user.id != user_id:
            abort(401)
        user = User.query.get_or_abort(
            user_id, error_msg=USER_NOT_FOUND.format(user_id)
        )
        if 'username' in args['user']:
            if (user.username != args['user']['username'] and
                    User.query.filter_by(
                        username=args['user']['username']
                    ).first()):  # noqa
                abort(400, status='error', code=400, message=USER_NAME_EXISTS)
            else:
                user.username = args['user']['username']
        if 'email' in args['user']:
            if (user.email != args['user']['email'] and
                    User.query.filter_by(
                        email=args['user']['email']
                    ).first()):  # noqa
                abort(400, status='error', code=400, message=USER_EMAIL_EXISTS)
            else:
                user.email = args['user']['email']
        if 'password' in args['user']:
            user.password = user.hash_password(args['user']['password'])
        db.session.commit()
        res = self.user_schema.dump(user)
        return res.data

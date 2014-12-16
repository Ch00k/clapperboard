from flask.ext.restful import Resource, abort

from webargs import Arg
from webargs.flaskparser import use_args

from clapperboard.resources.common.schemas import UserSchema

from clapperboard.resources.common.arg_validators import (
    user_json_validator
)

from clapperboard.models import db
from clapperboard.models.user import User


user_json = {
    'user': Arg(
        dict, target='json', required=True, validate=user_json_validator
    )
}


class UserAPI(Resource):
    def __init__(self):
        super(UserAPI, self).__init__()
        self.user_schema = UserSchema()

    @use_args(user_json)
    def post(self, args):
        print(args)
        email = args['user'].get('email', None)
        if User.query.filter_by(username=args['user']['username']).first():
            abort(
                400, status='error', code=400,
                message='User with that username already exists'
            )
        if email and User.query.filter_by(email=email).first():
            abort(
                400, status='error', code=400,
                message='User with that email already exists'
            )
        db.session.add(
            User(
                username=args['user']['username'],
                email=email,
                password=args['user']['password']
            )
        )
        db.session.commit()

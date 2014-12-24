from flask import current_app

from flask.ext.restful import Resource, abort
from flask.ext.jwt import current_user

from webargs import Arg
from webargs.flaskparser import use_args

from itsdangerous import BadSignature

from clapperboard.resources.common.schemas import UserSchema
from clapperboard.resources.common.errors import (
    USER_NOT_FOUND,
    USER_NAME_EXISTS,
    USER_EMAIL_EXISTS,
    EMAIL_ALREADY_VERIFIED,
    INVALID_EMAIL_V10N_CODE
)
from clapperboard.resources.common.messages import VERIFICATION_EMAIL_BODY
from clapperboard.resources.common.arg_validators import (
    user_create_json_validator,
    user_edit_json_validator
)
from clapperboard.resources.common import get_serializer
from clapperboard.models import db
from clapperboard.models.user import User
from clapperboard.mailer import mailer


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
        if User.query.filter_by(username=args['user']['username']).first():
            abort(400, status='error', code=400, message=USER_NAME_EXISTS)
        if User.query.filter_by(email=args['user']['email']).first():
            abort(400, status='error', code=400, message=USER_EMAIL_EXISTS)
        user = User(
            username=args['user']['username'],
            email=args['user']['email'],
            password=args['user']['password']
        )
        db.session.add(user)
        db.session.commit()

        s = get_serializer()
        payload = s.dumps(args['user']['email'])

        from clapperboard.resources import user_verify_email_url
        email = dict(
            to=args['user']['email'],
            subject='Clapperboard user activation',
            text=VERIFICATION_EMAIL_BODY.format(
                user_verify_email_url(payload=payload)
            )
        )
        email['h:X-Mailgun-Native-Send'] = True
        # TODO: Make this async
        mailer.send_email(**email)

        res = self.user_schema.dump(user)
        return res.data


class UserVerifyEmailAPI(Resource):
    def __init__(self):
        super(UserVerifyEmailAPI, self).__init__()

    def get(self, payload):
        s = get_serializer()
        try:
            user_email = s.loads(
                payload,
                salt=current_app.config['EMAIL_V10N_SALT'],
                max_age=current_app.config['EMAIL_V10N_MAX_AGE']
            )
        except BadSignature:
            abort(404)

        user = User.query.filter_by(email=user_email).first()
        if not user:
            abort(404, status='error', code=404,
                  message=INVALID_EMAIL_V10N_CODE)
        if not user.email_verified:
            user.email_verified = True
            db.session.commit()
            return {
                'code': 200, 'status': 'success', 'message': 'Email verified'
            }
        else:
            # TODO: 400 is not quite correct here
            abort(
                400, status='error', code=400, message=EMAIL_ALREADY_VERIFIED
            )


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
            user.password = args['user']['password']
        db.session.commit()
        res = self.user_schema.dump(user)
        return res.data

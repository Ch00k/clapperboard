import re

from webargs.core import ValidationError, __type_map__, text_type

from clapperboard.resources.common.errors import (
    TYPE_MISMATCH,
    EMAIL_INVALID,
    USERNAME_INVALID,
    PASSWORD_INVALID,
    PARAM_NOT_IN_OBJECT
)


def imdb_data_json_validator(val):
    _validate_params('imdb_data', val, id=int)


def movie_list_q_params_validator(val):
    if val not in ('empty', 'non_empty'):
        # TODO: Refactor this when more errors of this type are added
        msg = ('Invalid value "{}" for filter parameter "imdb_data". '
               'Supported values are "empty", "non_empty"'.format(val))
        _validation_error(msg)


def movie_metadata_json_validator(val):
    if ('tracker_ignore_imdb_not_found' in val and
            not isinstance(val['tracker_ignore_imdb_not_found'], bool)):
        _validation_error(
            TYPE_MISMATCH.format(
                __type_map__[bool],
                'tracker_ignore_imdb_not_found',
                __type_map__[type(val['tracker_ignore_imdb_not_found'])]
            )
        )


def user_create_json_validator(val):
    _validate_params('user', val, username=text_type, email=text_type,
                     password=text_type)
    if len(val['username']) < 3:
        _validation_error(USERNAME_INVALID)
    if len(val['password']) < 8:
        _validation_error(PASSWORD_INVALID)
    if not _email_valid(val['email']):
        _validation_error(EMAIL_INVALID.format(val['email']))


def user_edit_json_validator(val):
    if 'password' in val and len(val['password']) < 8:
        _validation_error(PASSWORD_INVALID)
    if not _email_valid(val['email']):
        _validation_error(EMAIL_INVALID.format(val['email']))


def _email_valid(email):
    return re.match(r'[^@]+@[^@]+\.[^@]+', email)


def _validation_error(msg):
    raise ValidationError(msg, status_code=400, message=msg)


def _validate_params(obj_name, val, **params):
    for param in params:
        if param not in val:
            _validation_error(PARAM_NOT_IN_OBJECT.format(param, obj_name))
        if not isinstance(val[param], params[param]):
            _validation_error(
                TYPE_MISMATCH.format(
                    __type_map__[params[param]], param,
                    __type_map__[type(val[param])]
                )
            )

import re

from webargs.core import ValidationError, __type_map__, text_type

from clapperboard.resources.common.errors import (
    TYPE_MISMATCH,
    EMAIL_INVALID,
    PASSWORD_INVALID,
    PARAM_NOT_IN_USER_OBJECT,
    PARAM_NOT_IN_IMDB_DATA_OBJECT
)


def imdb_data_json_validator(val):
    if 'id' not in val:
        _validation_error(PARAM_NOT_IN_IMDB_DATA_OBJECT.format('id'))
    if not isinstance(val['id'], int):
        _validation_error(
            TYPE_MISMATCH.format(
                __type_map__[int], 'id',
                __type_map__[type(val['id'])]
            )
        )


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
    params = ('username', 'password')
    msg = PARAM_NOT_IN_USER_OBJECT
    for param in params:
        if param not in val:
            _validation_error(msg.format(param))
        if not isinstance(val[param], text_type):
            _validation_error(
                TYPE_MISMATCH.format(
                    __type_map__[text_type],
                    param,
                    __type_map__[type(val[param])]
                )
            )
    if len(val['password']) < 8:
        _validation_error(PASSWORD_INVALID)
    if 'email' in val:
        if not _email_valid(val['email']):
            _validation_error(EMAIL_INVALID.format(val['email']))


def user_edit_json_validator(val):
    if 'password' in val and len(val['password']) < 8:
        _validation_error(PASSWORD_INVALID)
    if 'email' in val:
        if not _email_valid(val['email']):
            _validation_error(EMAIL_INVALID.format(val['email']))


def _email_valid(email):
    return re.match(r'[^@]+@[^@]+\.[^@]+', email)


def _validation_error(msg):
    raise ValidationError(msg, status_code=400, message=msg)

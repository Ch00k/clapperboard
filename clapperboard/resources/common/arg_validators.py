from webargs.core import ValidationError, __type_map__, text_type


def imdb_data_json_validator(val):
    if 'id' not in val:
        msg = "Required parameter 'id' not found in imdb_data object"
        _validation_error(msg)
    if not isinstance(val['id'], int):
        msg = 'Expected type {} for id, got {}'.format(
            __type_map__[int],
            __type_map__[type(val['id'])]
        )
        _validation_error(msg)


def movie_list_q_params_validator(val):
    if val not in ('empty', 'non_empty'):
        msg = ('Invalid value "{}" for filter parameter "imdb_data". '
               'Supported values are "empty", "non_empty"'.format(val))
        _validation_error(msg)


def user_json_validator(val):
    params = ('username', 'password')
    msg = "Required parameter '{}' not found in user object"
    for param in params:
        if param not in val:
            msg = msg.format(param)
            _validation_error(msg)
        if not isinstance(val[param], text_type):
            msg = 'Expected type {} for {}, got {}'.format(
                __type_map__[text_type],
                __type_map__[type(val[param])]
            )
    if len(val['password']) < 8:
        msg = "Password length must be 8 or more characters"
        _validation_error(msg)
    if 'email' in val:
        # TODO: Validate email address correctness
        pass


def _validation_error(msg):
    raise ValidationError(msg, status_code=400, message=msg)

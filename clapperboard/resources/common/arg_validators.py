from webargs.core import ValidationError, __type_map__


def imdb_data_json_validator(val):
    if 'id' not in val:
        msg = "Required parameter 'id' not found in imdb_data object"
        raise ValidationError(msg, status_code=400, message=msg)
    if not isinstance(val['id'], int):
        msg = 'Expected type {} for id, got {}'.format(
            __type_map__[int],
            __type_map__[type(val['id'])]
        )
        raise ValidationError(msg, status_code=400, message=msg)


def movie_list_q_params_validator(val):
    if val not in ('empty', 'non_empty'):
        msg = ('Invalid value "{}" for filter parameter "imdb_data". '
               'Supported values are "empty", "non_empty"'.format(val))
        raise ValidationError(msg, status_code=400, message=msg)

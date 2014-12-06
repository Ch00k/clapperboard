from webargs.core import ValidationError, __type_map__


def imdb_data_validator(val):
    if 'id' not in val:
        msg = "Required parameter 'id' not found in imdb_data object"
        raise ValidationError(msg, status_code=400, message=msg)
    if not isinstance(val['id'], int):
        msg = 'Expected type {} for id, got {}'.format(
            __type_map__[int],
            __type_map__[type(val['id'])]
        )
        raise ValidationError(msg, status_code=400, message=msg)

def imdb_data_data_type(data):
    if isinstance(data, dict):
        if data.get('id'):
            return data
    raise ValueError('Malformed request body')

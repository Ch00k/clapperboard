from flask.ext.restful import fields


IMDB_DATA = {
    'id': fields.Integer,
    'title': fields.String,
    'genre': fields.String,
    'country': fields.String,
    'director': fields.String,
    'cast': fields.String,
    'runtime': fields.Integer,
    'rating': fields.Float,
}


MOVIE = {
    'id': fields.Integer,
    'title': fields.String,
    'url_code': fields.String,
    'show_start': fields.String,
    'show_end': fields.String,
    'imdb_data': fields.Nested(IMDB_DATA, default={})
}


SHOW_TIME = {
    'id': fields.Integer,
    'theatre_id': fields.Integer,
    'hall_id': fields.Integer,
    'technology_id': fields.Integer,
    'date_time': fields.DateTime(dt_format='iso8601'),
    'order_url': fields.String
}


THEATRE = {
    'id': fields.Integer,
    'name': fields.String,
    'en_name': fields.String,
    'url_code': fields.String,
    'st_url_code': fields.String
}


TECHNOLOGY = {
    'id': fields.Integer,
    'code': fields.String,
    'name': fields.String
}

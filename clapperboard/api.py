import copy
import datetime
import os

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.restful import Api, Resource, fields, marshal, abort, reqparse

from sqlalchemy import or_

from helpers import get_movie_imdb_data


app = Flask(__name__)
api = Api(app)
app.config.from_object('clapperboard.config.api')
if os.environ.get('CB_API_SETTINGS'):
    app.config.from_envvar('CB_API_SETTINGS')
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    show_start = db.Column(db.DateTime)
    show_end = db.Column(db.DateTime)
    url = db.Column(db.String(255))
    imdb_data = db.relationship('IMDBData', uselist=False)
    show_times = db.relationship('ShowTime')

    def __init__(self, id, title, show_start, show_end, url):
        self.id = id
        self.title = title
        self.show_start = show_start
        self.show_end = show_end
        self.url = url

    def __repr__(self):
        return '<PKMovie %r, %r>' % (self.id, self.title)


class IMDBData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    rating = db.Column(db.Float)
    pk_movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))

    def __init__(self, id, title, rating, pk_movie_id):
        self.id = id
        self.title = title
        self.rating = rating
        self.pk_movie_id = pk_movie_id

    def __repr__(self):
        return '<IMDBMovie %r, %r>' % (self.id, self.title)


class ShowTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_time = db.Column(db.DateTime)
    hall_id = db.Column(db.Integer)
    technology = db.Column(db.String(8))
    order_url = db.Column(db.String(255))
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))

    def __init__(self, id, date_time, hall_id, technology, order_url, movie_id):
        self.id = id
        self.date_time = date_time
        self.hall_id = hall_id
        self.technology = technology
        self.order_url = order_url
        self.movie_id = movie_id

    def __repr__(self):
        return '<ShowTime %r, %r>' % (self.id, self.date_time)


imdb_data_fields = {
    'id': fields.Integer,
    'title': fields.String,
    'rating': fields.Float,
}


show_time_fields = {
    'id': fields.Integer,
    'date_time': fields.DateTime,
    'hall_id': fields.Integer,
    'technology': fields.String,
    'order_url': fields.String
}


movie_fields = {
    'id': fields.Integer,
    'title': fields.String,
    'show_start': fields.DateTime,
    'show_end': fields.DateTime,
    'url': fields.String,
}


def movie_data_type(data):
    if isinstance(data, dict):
        if data.get('imdb_data'):
            if data['imdb_data'].get('id'):
                return data
    raise ValueError('Malformed request body')


class MovieListAPI(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('imdb_data', type=str)
        self.parser.add_argument('show_times', type=str)
        super(MovieListAPI, self).__init__()

    def get(self):
        args = self.parser.parse_args()
        m_fields = copy.copy(movie_fields)

        if args['imdb_data']:
            m_fields['imdb_data'] = fields.Nested(imdb_data_fields)
        if args['show_times']:
            m_fields['show_times'] = fields.Nested(show_time_fields)

        return {'movies': marshal(get_current_movies(), m_fields)}


class MovieAPI(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        super(MovieAPI, self).__init__()

    def get(self, movie_id):
        movie = Movie.query.filter_by(id=movie_id).first()

        if not movie:
            abort(404, message='Movie {} not found'.format(movie_id))

        self.parser.add_argument('imdb_data', type=str, location='args')
        self.parser.add_argument('showtimes', type=str, location='args')
        args = self.parser.parse_args()

        m_fields = copy.copy(movie_fields)

        if args['imdb_data']:
            m_fields['imdb_data'] = fields.Nested(imdb_data_fields)
        if args['showtimes']:
            m_fields['show_times'] = fields.Nested(show_time_fields)

        return {'movie': marshal(movie, m_fields)}

    def put(self, movie_id):
        movie = Movie.query.filter_by(id=movie_id).first()

        if not movie:
            abort(404, message='Movie {} not found'.format(movie_id))

        self.parser.add_argument('movie', type=movie_data_type, location='json', required=True)
        args = self.parser.parse_args()

        imdb_id = args['movie']['imdb_data']['id']
        imdb_movie = get_movie_imdb_data(id=imdb_id)
        imdb_data_record = IMDBData(*imdb_movie + (movie_id,))

        if not IMDBData.query.filter_by(id=imdb_movie[0]).first():
            db.session.add(imdb_data_record)
        if movie.title != imdb_movie[1]:
            movie.title = imdb_movie[1]

        db.session.commit()

        return 200


# class MovieIMDBDataAPI(Resource):
#     def get(self, movie_id):
#         movie = Movie.query.filter_by(id=movie_id).first()
#         if not movie:
#             abort(404, message='Movie {} not found'.format(movie_id))
#         imdb_data = movie.imdb_data
#         if imdb_data:
#             resp = {'imdb_data': marshal(imdb_data, imdb_data_fields)}
#         else:
#             resp = {'imdb_data': {}}
#
#         return resp
#
#
# class MovieShowTimesAPI(Resource):
#     def get(self, movie_id):
#         movie = Movie.query.filter_by(id=movie_id).first()
#         if not movie:
#             abort(404, message='Movie {} not found'.format(movie_id))
#         showtime_data = movie.show_times
#         if showtime_data:
#             resp = {'showtimes': marshal(showtime_data, show_time_fields)}
#         else:
#             resp = {'showtimes': []}
#
#         return resp


def get_current_movies(show_start_within_days=14):
    """
    Get list of PK movies that are currently being shown or will start to be shown
    in the nearest days

    :param show_start_within_days: number of days in future that movie show should
                                   start within
    :return: List of PK movie objects
    """
    today = datetime.date.today()
    show_start_last_day = today + datetime.timedelta(show_start_within_days)

    movies_list = Movie.query.filter(Movie.show_start != None) \
        .filter(Movie.show_start <= show_start_last_day) \
        .filter(or_(Movie.show_end == None, Movie.show_end >= today)).all()

    return movies_list


api.add_resource(MovieListAPI, '/movies')
api.add_resource(MovieAPI, '/movies/<int:movie_id>')
# api.add_resource(MovieIMDBDataAPI, '/movies/<int:movie_id>/imdb-data')
# api.add_resource(MovieShowTimesAPI, '/movies/<int:movie_id>/showtimes')


if __name__ == '__main__':
    db.create_all()
    app.run()

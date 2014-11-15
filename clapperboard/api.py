import copy
import os
import time

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.restful import Api, Resource, fields, marshal, abort, reqparse
from flask.ext.restful.fields import get_value, Nested
from flask.ext.cors import CORS

from helpers import get_movie_imdb_data


app = Flask(__name__)
api = Api(app)
app.config.from_object('config.api')
if os.environ.get('CB_API_SETTINGS'):
    app.config.from_envvar('CB_API_SETTINGS')
db = SQLAlchemy(app)
cors = CORS(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    title = db.Column(db.String(255))
    show_start = db.Column(db.Integer)
    show_end = db.Column(db.Integer)
    url = db.Column(db.String(255))
    imdb_data = db.relationship('IMDBData', uselist=False)
    # TODO: Make this a dynamic relationship
    show_times = db.relationship('ShowTime')

    def __init__(self, id, title, show_start, show_end, url):
        self.id = id
        self.title = title
        self.show_start = show_start
        self.show_end = show_end
        self.url = url

    def __repr__(self):
        return '<Movie %r, %r>' % (self.id, self.title)


class IMDBData(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    title = db.Column(db.String(255))
    rating = db.Column(db.Float)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))

    def __init__(self, id, title, rating, movie_id):
        self.id = id
        self.title = title
        self.rating = rating
        self.movie_id = movie_id

    def __repr__(self):
        return '<IMDBMovie %r, %r>' % (self.id, self.title)


class ShowTime(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    date_time = db.Column(db.Integer)
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
    'date_time': fields.Integer,
    'hall_id': fields.Integer,
    'technology': fields.String,
    'order_url': fields.String
}


movie_fields = {
    'id': fields.Integer,
    'title': fields.String,
    'show_start': fields.Integer(default=None),
    'show_end': fields.Integer(default=None),
    'url': fields.String,
}


class NestedWithEmpty(Nested):
    """
    Allows returning an empty dictionary if marshaled value is None
    """
    def __init__(self, nested, allow_empty=False, **kwargs):
        self.allow_empty = allow_empty
        super(NestedWithEmpty, self).__init__(nested, **kwargs)

    def output(self, key, obj):
        value = get_value(key if self.attribute is None else self.attribute, obj)
        if value is None:
            if self.allow_null:
                return None
            elif self.allow_empty:
                return {}

        return marshal(value, self.nested)


def movie_data_type(data):
    if isinstance(data, dict):
        if data.get('imdb_data'):
            if data['imdb_data'].get('id'):
                return data
    raise ValueError('Malformed request body')


class MovieListAPI(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        super(MovieListAPI, self).__init__()

    def get(self):
        self.parser.add_argument('imdb_data', type=str, location='args')
        #self.parser.add_argument('current', type=str, location='args')
        self.parser.add_argument('show_times', type=str, location='args')
        self.parser.add_argument('starting_within_days', type=int, location='args')
        args = self.parser.parse_args()

        m_fields = copy.copy(movie_fields)

        # TODO: Return empty object if movie.imdb_data = None
        if args['imdb_data']:
            m_fields['imdb_data'] = NestedWithEmpty(imdb_data_fields, allow_empty=True)
        if args['show_times']:
            m_fields['show_times'] = NestedWithEmpty(show_time_fields, allow_empty=True)

        if args['starting_within_days']:
            movies = get_movies(current=True,
                                starting_within_days=args['starting_within_days'])
        else:
            movies = get_movies(current=True)

        return {'movies': marshal(movies, m_fields)}


class MovieAPI(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        super(MovieAPI, self).__init__()

    def get(self, movie_id):
        movie = Movie.query.filter_by(id=movie_id).first()

        if not movie:
            abort(404, message='Movie {} not found'.format(movie_id))

        self.parser.add_argument('imdb_data', type=str, location='args')
        self.parser.add_argument('show_times', type=str, location='args')

        args = self.parser.parse_args()

        m_fields = copy.copy(movie_fields)

        if args['imdb_data']:
            m_fields['imdb_data'] = NestedWithEmpty(imdb_data_fields, allow_empty=True)
        if args['show_times']:
            m_fields['show_times'] = NestedWithEmpty(show_time_fields, allow_empty=True)

        return {'movie': marshal(movie, m_fields)}

    # TODO: Make this call asynchronous
    def put(self, movie_id):
        self.parser.add_argument('X-Auth-Token', type=str, location='headers',
                                 required=True)
        args = self.parser.parse_args()

        if not args['X-Auth-Token'] == app.config['AUTH_TOKEN']:
            abort(401)

        movie = Movie.query.filter_by(id=movie_id).first()

        if not movie:
            abort(404, message='Movie {} not found'.format(movie_id))

        self.parser.add_argument('movie', type=movie_data_type, location='json',
                                 required=True)
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


def get_movies(**kwargs):
    """
    Get list of movies filtering by various criteria

    :param kwargs: current: show only movies whose show end date is later than now
                   starting_within_days: show only movies whose show start date is no
                   later than starting_within_days value
    :return:
    """
    now = int(time.time())
    all_movies = Movie.query
    movies = all_movies

    if kwargs.get('current'):
        movies = movies.filter(db.or_(Movie.show_end == None, Movie.show_end >= now))

    if kwargs.get('starting_within_days'):
        starting_within_seconds = kwargs['starting_within_days'] * 24 * 60 * 60
        movies = movies.filter(Movie.show_start != None)\
            .filter(Movie.show_start <= now + starting_within_seconds)

    return movies.all()


api.add_resource(MovieListAPI, '/movies')
api.add_resource(MovieAPI, '/movies/<int:movie_id>')


if __name__ == '__main__':
    app.run()

#https://cabinet.planeta-kino.com.ua/hall-scheme/?theater=pk-lvov&showtime=72839
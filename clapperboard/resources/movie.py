from flask.ext.restful import Resource, marshal_with, marshal


from flask import jsonify
from webargs import Arg, flaskparser
from webargs.flaskparser import use_args

from flask.ext.restful import abort

from clapperboard.models import db
from clapperboard.models.movie import Movie
from clapperboard.models.imdb_data import IMDBData
from clapperboard.models.show_time import ShowTime

from clapperboard.resources.common import marshal_with_key
from clapperboard.resources.common.response_fields import (
    MOVIE,
    IMDB_DATA,
    SHOW_TIME,
    MovieSchema
)
from clapperboard.resources.common.errors import MOVIE_NOT_FOUND
from clapperboard.resources.common.data_types import imdb_data_data_type

from clapperboard.common.utils import get_movie_imdb_data


class MovieListAPI(Resource):
    def __init__(self):
        super(MovieListAPI, self).__init__()

    #@marshal_with(MOVIE, envelope='movies')
    def get(self):
        schema = MovieSchema(many=True)
        movies = Movie.query.all()
        res = schema.dump(movies)
        print res
        return res.data


class MovieAPI(Resource):
    def __init__(self):
        super(MovieAPI, self).__init__()

    #@marshal_with(MOVIE, envelope='movie')
    def get(self, movie_id):
        movie = Movie.query.get_or_abort(
            movie_id, error_msg=MOVIE_NOT_FOUND.format(movie_id)
        )
        schema = MovieSchema()
        res = schema.dump(movie)
        return res.data


imdb_data_json = {'imdb_data': Arg(dict, required=True)}


class MovieIMDBDataAPI(Resource):
    def __init__(self):
        super(MovieIMDBDataAPI, self).__init__()

    @marshal_with(IMDB_DATA, default={}, envelope='imdb_data')
    def get(self, movie_id):
        movie = Movie.query.get_or_abort(
            movie_id, error_msg=MOVIE_NOT_FOUND.format(movie_id)
        )
        return movie.imdb_data

    # TODO: Make this call async
    @use_args(imdb_data_json, targets=('json',))
    def put(self, args, movie_id):
        print args
        # movie = Movie.query.get_or_abort(movie_id,
        #                                  error_msg=MOVIE_NOT_FOUND.format(movie_id))
        # imdb_id = args['imdb_data']['id']
        #
        # movie_imdb_data = get_movie_imdb_data(id=imdb_id)
        # print movie_imdb_data
        # for key in movie_imdb_data:
        #     setattr(movie.imdb_data, key, movie_imdb_data[key])
        # db.session.commit()
        #
        # return 200


class MovieShowTimesAPI(Resource):
    def __init__(self):
        super(MovieShowTimesAPI, self).__init__()

    def get(self, movie_id):
        movie = Movie.query.get_or_abort(
            movie_id, error_msg=MOVIE_NOT_FOUND.format(movie_id)
        )
        show_times = movie.show_times.all()
        return {'show_times': marshal(show_times, SHOW_TIME)}

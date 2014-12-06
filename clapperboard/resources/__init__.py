from flask.ext.restful import Api, abort
from flask.ext.restful.representations.json import settings as json_settings

from flask.ext.cors import CORS

from webargs.flaskparser import parser

from clapperboard.resources.movie import (
    MovieAPI,
    MovieListAPI,
    MovieIMDBDataAPI,
    MovieShowTimesListAPI,
    MovieShowTimeAPI
)
from clapperboard.resources.showtime import ShowTimeAPI, ShowTimesListAPI
from clapperboard.resources.theatre import TheatreAPI, TheatreListAPI
from clapperboard.resources.technology import TechnologyAPI, TechnologyListAPI


api = Api()
cors = CORS()

api.add_resource(MovieListAPI, '/movies')
api.add_resource(MovieAPI, '/movies/<int:movie_id>')
api.add_resource(MovieIMDBDataAPI, '/movies/<int:movie_id>/imdb-data')
api.add_resource(MovieShowTimesListAPI, '/movies/<int:movie_id>/showtimes')
api.add_resource(MovieShowTimeAPI,
                 '/movies/<int:movie_id>/showtimes/<int:showtime_id>')
api.add_resource(ShowTimesListAPI, '/showtimes')
api.add_resource(ShowTimeAPI, '/showtimes/<int:showtime_id>')
api.add_resource(TheatreListAPI, '/theatres', '/theatres/')
api.add_resource(TheatreAPI, '/theatres/<int:theatre_id>')
api.add_resource(TechnologyListAPI, '/technologies')
api.add_resource(TechnologyAPI, '/technologies/<int:technology_id>')

json_settings['indent'] = 4


@parser.error_handler
def handle_request_parsing_error(err):
    """
    webargs error handler that uses Flask-RESTful's abort function to return
    a JSON error response to the client.
    """
    code, msg = (
        getattr(err, 'status_code', 400), getattr(err, 'message',
                                                  'Invalid Request')
    )
    abort(code, status='error', code=code, message=msg)

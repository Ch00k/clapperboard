import os

from flask import Flask
from flask.ext.restful import Api
from flask.ext.cors import CORS


app = Flask(__name__)
api = Api(app)
app.config.from_object('clapperboard.config.api')

if os.environ.get('CB_API_SETTINGS'):
    app.config.from_envvar('CB_API_SETTINGS')
cors = CORS(app)


from clapperboard.resources.movie import *
from clapperboard.resources.theatre import *
from clapperboard.resources.technology import *

api.add_resource(MovieListAPI, '/movies', '/movies/')
api.add_resource(MovieAPI, '/movies/<int:movie_id>', '/movies/<int:movie_id>/')

api.add_resource(MovieIMDBDataAPI, '/movies/<int:movie_id>/imdb-data',
                 '/movies/<int:movie_id>/imdb-data/')
api.add_resource(MovieShowTimesAPI, '/movies/<int:movie_id>/showtimes',
                 '/movies/<int:movie_id>/showtimes/')

api.add_resource(TheatreListAPI, '/theatres', '/theatres/')
api.add_resource(TheatreAPI, '/theatres/<int:theatre_id>', '/theatres/<int:theatre_id>/')

api.add_resource(TechnologyListAPI, '/technologies', '/technologies/')
api.add_resource(TechnologyAPI, '/technologies/<int:technology_id>',
                 '/technologies/<int:technology_id>/')


from flask.ext.restful import Api
from flask.ext.cors import CORS
from flask.ext.restful.representations.json import settings as json_settings

from clapperboard.resources.movie import *
from clapperboard.resources.theatre import *
from clapperboard.resources.technology import *

api = Api()
cors = CORS()

api.add_resource(MovieListAPI, '/movies')
api.add_resource(MovieAPI, '/movies/<int:movie_id>')
api.add_resource(MovieIMDBDataAPI, '/movies/<int:movie_id>/imdb-data')
api.add_resource(MovieShowTimesAPI, '/movies/<int:movie_id>/showtimes')
api.add_resource(TheatreListAPI, '/theatres', '/theatres/')
api.add_resource(TheatreAPI, '/theatres/<int:theatre_id>')
api.add_resource(TechnologyListAPI, '/technologies')
api.add_resource(TechnologyAPI, '/technologies/<int:technology_id>')

json_settings['indent'] = 4

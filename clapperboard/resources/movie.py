import json

from flask.ext.restful import Resource, abort

from webargs import Arg
from webargs.flaskparser import use_args

from clapperboard.resources.common import admin_required
from clapperboard.resources.common.schemas import (
    MovieSchema,
    IMDBDataSchema,
    ShowTimeSchema
)
from clapperboard.models import db
from clapperboard.models.movie import Movie
from clapperboard.models.movie_metadata import MovieMetadata
from clapperboard.models.imdb_data import IMDBData
from clapperboard.models.show_time import ShowTime


from clapperboard.resources.common.errors import (
    MOVIE_NOT_FOUND,
    SHOWTIME_NOT_FOUND
)

from clapperboard.resources.common.arg_validators import (
    imdb_data_json_validator,
    movie_list_q_params_validator,
    movie_metadata_json_validator
)

from clapperboard.common.utils import get_movie_imdb_data


movie_list_q_params = {
    'imdb_data': Arg(
        str, target='querystring', validate=movie_list_q_params_validator
    )
}

imdb_data_json = {
    'imdb_data': Arg(
        dict, target='json', required=True, validate=imdb_data_json_validator
    )
}

movie_metadata_create_json = {
    'metadata': Arg(
        dict, target='json', required=True,
        validate=movie_metadata_json_validator
    )
}

movie_metadata_edit_json = {
    'metadata': Arg(
        dict, target='json',
        validate=movie_metadata_json_validator
    )
}


class MovieListAPI(Resource):
    def __init__(self):
        super(MovieListAPI, self).__init__()
        self.movie_schema = MovieSchema(many=True)

    @use_args(movie_list_q_params)
    def get(self, args):
        movies = Movie.query
        if args['imdb_data'] == 'empty':
            movies = movies.filter(Movie.imdb_data == None)
        elif args['imdb_data'] == 'non_empty':
            movies = movies.filter(Movie.imdb_data != None)
        movies = movies.all()
        res = self.movie_schema.dump(movies)
        return res.data


class MovieAPI(Resource):
    def __init__(self):
        super(MovieAPI, self).__init__()
        self.movie_schema = MovieSchema()

    def get(self, movie_id):
        movie = Movie.query.get_or_abort(
            movie_id, error_msg=MOVIE_NOT_FOUND.format(movie_id)
        )
        res = self.movie_schema.dump(movie)
        return res.data


class MovieMetaDataAPI(Resource):
    def __init__(self):
        super(MovieMetaDataAPI, self).__init__()

    @admin_required
    def get(self, movie_id):
        movie = Movie.query.get_or_abort(
            movie_id, error_msg=MOVIE_NOT_FOUND.format(movie_id)
        )

        return {
            'metadata': json.loads(movie.meta.data) if movie.meta else {}
        }

    @admin_required
    @use_args(movie_metadata_create_json)
    def post(self, args, movie_id):
        movie = Movie.query.get_or_abort(
            movie_id, error_msg=MOVIE_NOT_FOUND.format(movie_id)
        )
        if movie.meta:
            abort(
                400, status='error', code=400,
                message='Metadata for movie {} already exists'
                .format(movie_id)
            )
        movie.meta = MovieMetadata(json.dumps(args['metadata']), movie_id)
        db.session.commit()
        return args

    @admin_required
    @use_args(movie_metadata_edit_json)
    def put(self, args, movie_id):
        movie = Movie.query.get_or_abort(
            movie_id, error_msg=MOVIE_NOT_FOUND.format(movie_id)
        )
        if not movie.meta:
            abort(
                404, status='error', code=404,
                message='Metadata for movie {} not found'.format(movie_id)
            )

        metadata_dict = json.loads(movie.meta.data) if movie.meta.data else {}

        # TODO: Won't work in Python 2
        for k, v in args['metadata'].items():
            metadata_dict[k] = v

        movie.meta.data = json.dumps(metadata_dict)
        db.session.commit()
        return {
            'metadata': json.loads(movie.meta.data) if movie.meta else {}
        }


class MovieIMDBDataAPI(Resource):
    def __init__(self):
        super(MovieIMDBDataAPI, self).__init__()
        self.imdb_data_schema = IMDBDataSchema()

    def get(self, movie_id):
        movie = Movie.query.get_or_abort(
            movie_id, error_msg=MOVIE_NOT_FOUND.format(movie_id)
        )
        res = self.imdb_data_schema.dump(movie.imdb_data)
        return res.data

    # TODO: Make this call async
    @admin_required
    @use_args(imdb_data_json)
    def post(self, args, movie_id):
        movie = Movie.query.get_or_abort(
            movie_id, error_msg=MOVIE_NOT_FOUND.format(movie_id)
        )

        if movie.imdb_data:
            abort(
                400, status='error', code=400,
                message='IMDB data for movie {} already exists'
                .format(movie_id)
            )

        imdb_id = args['imdb_data']['id']

        # TODO: Handle inexistent IMDB id
        # TODO: Handle already existing IMDB record
        imdb_data = IMDBData.query.get(args['imdb_data']['id'])
        if imdb_data:
            movie.imdb_data = imdb_data
        else:
            movie_imdb_data = get_movie_imdb_data(id=imdb_id)
            movie_imdb_data['movie_id'] = movie.id
            movie.imdb_data = IMDBData(**movie_imdb_data)
        db.session.commit()
        return 200

    @admin_required
    @use_args(imdb_data_json)
    def put(self, args, movie_id):
        movie = Movie.query.get_or_abort(
            movie_id, error_msg=MOVIE_NOT_FOUND.format(movie_id)
        )
        if not movie.imdb_data:
            abort(
                404, status='error', code=404,
                message='IMDB data for movie {} not found'.format(movie_id)
            )

        imdb_id = args['imdb_data']['id']
        if movie.imdb_data.id == imdb_id:
            return 200

        # TODO: Handle inexistent IMDB id
        # TODO: Handle already existing IMDB record
        movie_imdb_data = get_movie_imdb_data(id=imdb_id)
        for key in movie_imdb_data:
            setattr(movie.imdb_data, key, movie_imdb_data[key])
        db.session.commit()
        return 200


class MovieShowTimesListAPI(Resource):
    def __init__(self):
        super(MovieShowTimesListAPI, self).__init__()
        self.showtime_schema = ShowTimeSchema(many=True)

    def get(self, movie_id):
        movie = Movie.query.get_or_abort(
            movie_id, error_msg=MOVIE_NOT_FOUND.format(movie_id)
        )
        show_times = movie.show_times.all()
        res = self.showtime_schema.dump(show_times)
        return res.data


class MovieShowTimeAPI(Resource):
    def __init__(self):
        super(MovieShowTimeAPI, self).__init__()
        self.showtime_schema = ShowTimeSchema()

    def get(self, movie_id, showtime_id):
        Movie.query.get_or_abort(
            movie_id, error_msg=MOVIE_NOT_FOUND.format(movie_id)
        )
        show_time = ShowTime.query.get_or_abort(
            showtime_id, error_msg=SHOWTIME_NOT_FOUND.format(showtime_id)
        )
        res = self.showtime_schema.dump(show_time)
        return res.data

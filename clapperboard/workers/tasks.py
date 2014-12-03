from copy import copy
import logging

from clapperboard.models import db
from clapperboard.models.movie import Movie
from clapperboard.models.imdb_data import IMDBData
from clapperboard.models.show_time import ShowTime
from clapperboard.models.theatre import Theatre
from clapperboard.models.technology import Technology
from clapperboard.models.last_fetched import LastFetched
from clapperboard.common.utils import get_pk_data, get_movie_imdb_data

from clapperboard import celery_app


log = logging.getLogger(__name__)


def _insert_movie_record_imdb_data(record):
    imdb_query_title = record.url_code.replace('-', ' ')

    movie_imdb_data = get_movie_imdb_data(title=imdb_query_title)
    if movie_imdb_data:
        movie_imdb_data['movie_id'] = record.id
        record.imdb_data = IMDBData(**movie_imdb_data)
    else:
        log.warning('IMDB data not found')


def _update_movie_record_imdb_data(record):
    movie_imdb_data = get_movie_imdb_data(id=record.imdb_data.id)
    for key in movie_imdb_data:
        setattr(record.imdb_data, key, movie_imdb_data[key])


def _insert_movie_record(movie_data_dict):
    movie_dict = copy(movie_data_dict)
    movie_dict.pop('showtimes')
    movie_record = Movie(**movie_dict)

    # Set IMDB data for the movie
    imdb_query_title = movie_data_dict['url_code'].replace('-', ' ')
    movie_imdb_data = get_movie_imdb_data(title=imdb_query_title)

    if movie_imdb_data:
        movie_imdb_data['movie_id'] = movie_data_dict['id']
        movie_record.imdb_data = IMDBData(**movie_imdb_data)
    else:
        log.warning('IMDB data not found')

    # Set show times for the movie
    if movie_data_dict['showtimes']:
        show_times = []
        for show_time in movie_data_dict['showtimes']:
            show_time_dict = _compile_st_dict(show_time)
            show_times.append(ShowTime(**show_time_dict))
        movie_record.show_times = show_times

    db.session.add(movie_record)


def _update_movie_record(record, movie_data_dict):
    for key in movie_data_dict:
        if key != 'showtimes':
            setattr(record, key, movie_data_dict[key])


def _insert_movie_record_showtimes_data(record, showtimes_data):
    # If no show times for a movie found add them
    show_times = []
    for show_time in showtimes_data:
        show_time_dict = _compile_st_dict(show_time)
        show_times.append(ShowTime(**show_time_dict))
    record.show_times = show_times


def _update_movie_record_showtimes_data(record, showtimes_data):
    # If the record is found in db but is not XML delete the record
    record_show_times = record.show_times.all()
    for st_record in record_show_times:
        if st_record.id not in [movie_st['id'] for movie_st in showtimes_data]:
            record_show_times.remove(st_record)

    # If the movie record already has show times associated
    # add only those that are not there yet
    for show_time in showtimes_data:
        if show_time['id'] not in [st.id for st in record_show_times]:
            show_time_dict = _compile_st_dict(show_time)
            record_show_times.append(ShowTime(**show_time_dict))


# TODO: There must be a more efficient way to do that
def _compile_st_dict(st_dict):
    st_dict['theatre_id'] = Theatre.query.filter(
        Theatre.st_url_code == st_dict.pop('theatre')
    ).first().id

    st_dict['technology_id'] = Technology.query.filter(
        Technology.code == st_dict.pop('technology')
    ).first().id

    return st_dict


def _update_last_fetched(theatres_dict):
    for theatre in theatres_dict:
        Theatre.query.get(theatre['id']).last_fetched.date_time = theatre['last_fetched']
    db.session.commit()


@celery_app.task
def write_movie_data(force=False):
    """
    Create new or update existing movie record in database.

    :return:
    """
    theatres_dict = [dict(
        id=th.id,
        en_name=th.en_name,
        url_code=th.url_code,
        last_fetched=th.last_fetched.date_time
    ) for th in Theatre.query.all()]

    movies_data, theatres = get_pk_data(theatres_dict, force=force)
    if not movies_data:
        _update_last_fetched(theatres)
        log.info('No updated movie data found')
        return

    processed_movies = 0
    existing_movies = 0
    new_movies = 0

    for movie in movies_data:
        log.info('Processing movie: "{}"'.format(movie['url_code']))
        processed_movies += 1

        movie_record = Movie.query.filter_by(id=movie['id']).first()

        if movie_record:
            log.info('Existing movie, updating')
            existing_movies += 1

            _update_movie_record(movie_record, movie)

            if movie_record.imdb_data:
                _update_movie_record_imdb_data(movie_record)
            else:
                _insert_movie_record_imdb_data(movie_record)

            if movie['showtimes']:
                if movie_record.show_times.first():
                    _update_movie_record_showtimes_data(movie_record, movie['showtimes'])
                else:
                    _insert_movie_record_showtimes_data(movie_record, movie['showtimes'])
        else:
            log.info('New movie, adding')
            new_movies += 1
            _insert_movie_record(movie)

        db.session.commit()

    log.info('Movies processed: {}'.format(processed_movies))
    log.info('Movies already in db: {}'.format(existing_movies))
    log.info('New movies: {}'.format(new_movies))

    _update_last_fetched(theatres)

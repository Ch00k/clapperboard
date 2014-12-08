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


def _insert_movie_record(movie_data_dict):
    movie_record = Movie(**movie_data_dict)

    # Set IMDB data for the movie
    imdb_query_title = movie_data_dict['url_code'].replace('-', ' ')
    movie_imdb_data = get_movie_imdb_data(title=imdb_query_title)

    if movie_imdb_data:
        # TODO: Factor this (and all the below) into a function
        imdb_data = IMDBData.query.get(movie_imdb_data['id'])
        if imdb_data:
            movie_record.imdb_data = imdb_data
        else:
            movie_record.imdb_data = IMDBData(**movie_imdb_data)
    else:
        log.warning(
            'IMDB data not found for movie "{}"'
            .format(movie_data_dict['url_code'])
        )

    db.session.add(movie_record)


def _update_movie_record(record, movie_data_dict):
    for key in movie_data_dict:
        setattr(record, key, movie_data_dict[key])


def _insert_movie_record_imdb_data(record):
    imdb_query_title = record.url_code.replace('-', ' ')

    movie_imdb_data = get_movie_imdb_data(title=imdb_query_title)
    if movie_imdb_data:
        imdb_data = IMDBData.query.get(movie_imdb_data['id'])
        if imdb_data:
            record.imdb_data = imdb_data
        else:
            record.imdb_data = IMDBData(**movie_imdb_data)
    else:
        log.warning(
            'IMDB data not found for movie "{}"'.format(record.url_code)
        )


def _update_movie_record_imdb_data(record):
    movie_imdb_data = get_movie_imdb_data(id=record.imdb_data.id)
    imdb_data = IMDBData.query.get(movie_imdb_data['id'])
    if imdb_data:
        record.imdb_data = imdb_data
    else:
        for key in movie_imdb_data:
            setattr(record.imdb_data, key, movie_imdb_data[key])


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
        Theatre.query.get(theatre['id']).last_fetched.date_time = \
            theatre['last_fetched']
    db.session.commit()


@celery_app.task
def write_movie_data(force):
    """
    Create new or update existing movie record in database.

    :return:
    """
    theatres_dict = [
        dict(
            id=th.id,
            en_name=th.en_name,
            url_code=th.url_code,
            last_fetched=th.last_fetched.date_time
        ) for th in Theatre.query.all()
    ]

    movies_data, showtimes_data, theatres_data = get_pk_data(theatres_dict,
                                                             force=force)
    if not movies_data:
        _update_last_fetched(theatres_data)
        log.info('No updated movie data found')
        return

    existing_movies = Movie.query.count()
    new_movies = 0

    log.info('Updating movies')
    for movie in movies_data:
        movie_record = Movie.query.get(movie['id'])

        if movie_record:
            log.info('Updating existing movie "{}"'.format(movie['url_code']))
            _update_movie_record(movie_record, movie)

            if movie_record.imdb_data:
                _update_movie_record_imdb_data(movie_record)
            else:
                _insert_movie_record_imdb_data(movie_record)
        else:
            log.info('Adding new movie "{}"'.format(movie['url_code']))
            new_movies += 1
            _insert_movie_record(movie)

        db.session.commit()

    log.info('Movies processed: {}'.format(len(movies_data)))
    log.info('Existing movies: {}'.format(existing_movies))
    log.info('New movies: {}'.format(new_movies))

    existing_showtimes = ShowTime.query.count()
    new_showtimes = 0
    deleted_showtimes = 0

    log.info('Updating showtimes')
    showtime_ids = [st['id'] for st in showtimes_data]
    showtimes_to_delete = []
    showtimes_to_add = []

    for showtime in ShowTime.query.all():
        if showtime.id not in showtime_ids:
            showtimes_to_delete.append(showtime.id)
            deleted_showtimes += 1
    for showtime in showtimes_data:
        if not ShowTime.query.get(showtime['id']):
            showtimes_to_add.append(ShowTime(**_compile_st_dict(showtime)))
            new_showtimes += 1

    if showtimes_to_delete:
        ShowTime.query.filter(ShowTime.id.in_(showtimes_to_delete))\
            .delete(synchronize_session=False)

    if showtimes_to_add:
        db.session.add_all(showtimes_to_add)

    db.session.commit()

    log.info('Showtimes processed: {}'.format(len(showtimes_data)))
    log.info('Existing showtimes: {}'.format(existing_showtimes))
    log.info('New showtimes: {}'.format(new_showtimes))
    log.info('Deleted showtimes: {}'.format(deleted_showtimes))

    _update_last_fetched(theatres_data)

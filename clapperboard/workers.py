import logging as log
import os
import time

from apscheduler.schedulers.background import BackgroundScheduler

from api import db, Movie, IMDBData, ShowTime
from helpers import *
from config.workers import *


# TODO: Replace this hack with something more "humane"
if os.environ.get('CB_WORKERS_SETTINGS'):
    path = os.environ['CB_WORKERS_SETTINGS']
    execfile(path)

log.basicConfig(format='[%(asctime)s]: %(levelname)s: %(message)s',
                level=getattr(log, LOG_LEVEL), filename=LOG_FILE)


def write_movie_data():
    """
    Create new or update existing movie record in database.

    :return:
    """
    start_time = time.time()

    data = get_pk_data(XML_DATA_URL)
    show_times = data['showtimes']['day']

    processed_movies = 0
    existing_movies = 0
    new_movies = 0


    for movie in data['movies']['movie']:
        processed_movies += 1

        log.info('Found movie {} in XML'.format(movie['@url']))

        dt_start = string_to_datetime(movie['dt-start'])
        dt_end = string_to_datetime(movie['dt-end'])

        # See if the record with that id already exists
        record = Movie.query.filter_by(id=movie['@id']).first()

        if record:
            existing_movies += 1

            log.info('Movie already exists in db')

            # Update show start and end dates
            if record.show_start != dt_start:
                log.info('Show start date differs, updating')
                record.show_start = dt_start
            if record.show_end != dt_end:
                log.info('Show end date differs, updating')
                record.show_end = dt_end

            # See if it has IMDB data associated
            if record.imdb_data:
                # If it does update its rating
                log.info('Movie IMDB data already exists in db')
                movie_imdb_data = get_movie_imdb_data(id=record.imdb_data.id)
                if record.imdb_data.rating != movie_imdb_data[2]:
                    log.info('IMDB rating differs, updating')
                    record.imdb_data.rating = movie_imdb_data[2]
            else:
                # If not get movie data from IMDB
                pk_title = extract_title_from_pk_url(record.url)
                log.info('Movie IMDB data missing, '
                         'searching IMDB with title "{}"'.format(pk_title))
                movie_imdb_data = get_movie_imdb_data(title=pk_title)
                if movie_imdb_data:
                    log.info('Movie found on IMDB (id {}), '
                             'inserting'.format(movie_imdb_data[0]))
                    record.imdb_data = IMDBData(*movie_imdb_data + (record.id,))
                else:
                    log.info('Movie not found on IMDB')

            movie_showtimes_data = get_movie_showtimes_data(show_times, record.id)

            if movie_showtimes_data:
                log.info('Movie show times found in XML')
                # See if it has showtimes data associated
                if record.show_times:
                    # If the movie record already has show times associated
                    # add only those that are not there yet
                    log.info('Movie show times already exist in db, updating')
                    for show_time in movie_showtimes_data:
                        if not ShowTime.query.filter_by(id=show_time[0]):
                            record.show_times.append(ShowTime(*show_time))
                else:
                    # If no show times for a movie found add them
                    log.info('Movie show times missing, inserting')
                    record.show_times = \
                        [ShowTime(*show_time) for show_time in movie_showtimes_data]
            else:
                log.info('Movie show times not found in XML')
        else:
            new_movies += 1

            log.info('Movie not found in db, inserting')
            # Set IMDB data for the movie
            pk_title = extract_title_from_pk_url(movie['@url'])
            movie_imdb_data = get_movie_imdb_data(title=pk_title)

            if movie_imdb_data:
                log.info('Movie found on IMDB (id {}), '
                         'inserting'.format(movie_imdb_data[0]))
                pk_movie_record = Movie(movie['@id'], movie_imdb_data[1],
                                        dt_start, dt_end, movie['@url'])
                pk_movie_record.imdb_data = IMDBData(*movie_imdb_data + (movie['@id'],))
            else:
                log.info('Movie not found on IMDB')
                pk_movie_record = Movie(movie['@id'], pk_title.title(),
                                        dt_start, dt_end, movie['@url'])

            # Set show times for the movie
            log.info('Inserting movie show times')
            movie_showtimes_data = get_movie_showtimes_data(show_times, movie['@id'])
            if movie_showtimes_data:
                log.info('Movie show times found in XML, inserting')
                pk_movie_record.show_times = \
                    [ShowTime(*show_time) for show_time in movie_showtimes_data]
            else:
                log.info('Movie show times not found in XML')

            db.session.add(pk_movie_record)

        db.session.commit()

    end_time = time.time()
    log.info('Job took {} seconds'.format((end_time - start_time)))
    log.info('Movies processed: {}'.format(processed_movies))
    log.info('Movies already in db: {}'.format(existing_movies))
    log.info('New movies: {}'.format(new_movies))


def main():
    sched = BackgroundScheduler()

    # Add two jobs: one for immediate fetching of data (on start)
    # and another one hourly
    # TODO: Don't allow situations when cron and onetime jobs can run simultaneously
    sched.add_job(write_movie_data, name='write_movie_data_onetime')
    sched.add_job(write_movie_data, name='write_movie_data_periodic',
                  trigger='cron', hour='*/{}'.format(SCHED_TIME_HOURS))

    sched.start()
    while True:
        time.sleep(60)


if __name__ == '__main__':
    main()

import datetime
import logging as log
import re
import time
import unicodedata
import urllib2

import imdb
import xmltodict

from apscheduler.schedulers.background import BackgroundScheduler

from api import db, Movie, IMDBData, ShowTime


log.basicConfig(format='[%(asctime)s]: %(levelname)s: %(message)s', level=log.INFO,
                filename='/var/log/clapperboard/api.log')


def get_pk_data(city):
    """
    Get movies and showtimes data from PK website.

    :param city: City to get the data for
    :return: Dictionary containing all PK movies and showtimes data
    """
    url = 'http://planeta-kino.com.ua/{}/ua/showtimes/xml/'.format(city)
    data = urllib2.urlopen(url).read()
    data_dict = xmltodict.parse(data)

    return data_dict['planeta-kino']


def extract_title_from_pk_url(url):
    return url.split('/')[-2].replace('-', ' ')


def normalize_title(title):
    """
    Transform movie title so that it's ready for string comparison.

    Remove everything but alphanumeric chars from the string and replaces unicode
    characters with their ascii equivalents.

    :param title: Movie title
    :return: Normalized title
    """
    # Convert all unicode chars to ASCII
    ascii_title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore')

    # Remove all non-alnum chars
    pattern = re.compile('[\W_]+')
    normalized_title = pattern.sub('', ascii_title.lower())

    return normalized_title


def string_to_datetime(str):
    """
    Convert date string representation to datetime object

    :param str: Date string format
    :return: Datetime object
    """
    if str:
        # A dull check whether the string contains time
        if ':' in str:
            return datetime.datetime.strptime(str, '%Y-%m-%d %H:%M:%S')
        else:
            return datetime.datetime.strptime(str, '%Y-%m-%d')
    else:
        return None


def get_movie_showtimes_data(showtimes_struct, movie_id):
    """
    Get list of showtimes for a specific PK movie.

    :param showtimes_struct: Dictionary with showtimes data
    :param movie_id: PK movie id
    :return: List of showtime objects
    """
    order_url_pattern = \
        '^https:\/\/cabinet.planeta-kino.com.ua\/hall\/\?show_id=(\d+)&.*$'
    movie_show_times = []
    for show_time in showtimes_struct:
        for show in show_time['show']:
            if show['@movie-id'] == str(movie_id):
                if show['@order-url']:
                    show_time_id = \
                        re.match(order_url_pattern, show['@order-url']).group(1)
                    show_time_datetime = string_to_datetime(show['@full-date'])
                    movie_show_times.append((int(show_time_id), show_time_datetime,
                                             show['@hall-id'], show['@technology'],
                                             show['@order-url'], movie_id))
    return movie_show_times


def write_movie_data(db):
    """
    Create new or update existing movie record in database.

    :param db: An instance of SQLAlchemy of Flask app
    :return:
    """
    start_time = time.time()

    data = get_pk_data('lvov')
    show_times = data['showtimes']['day']

    for movie in data['movies']['movie']:

        log.info('Found movie {} in XML'.format(movie['@url']))

        dt_start = string_to_datetime(movie['dt-start'])
        dt_end = string_to_datetime(movie['dt-end'])

        # See if the record with that id already exists
        record = Movie.query.filter_by(id=movie['@id']).first()

        if record:
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


def titles_match(pk_title, imdb_title):
    """
    Try to find a match between a PK title and an IMDB title.

    First triy a simple string equality, then add a 'the' to PK title,
    then remove 'the' from pk_title if it exists, then remove all 'and' occurrences
    from PK title.

    :param pk_title: Title retrieved from PK movie URL
    :param imdb_title: Title of the movie found on IMDB
    :return: True if titles match, False otherwise
    """
    return ((pk_title == imdb_title) or
            ('the' + pk_title == imdb_title) or
            (pk_title.startswith('the') and pk_title[3:] == imdb_title) or
            (pk_title.replace('and', '') == imdb_title))


def get_movie_imdb_data(**kwargs):
    """
    Retrieve IMDB info about a movie either by its PK title or by IMDB id.

    :param kwargs: Either title or IMDB id
    :return: Tuple with IMDB movie data, None otherwise
    """
    imdb_cl = imdb.IMDb()
    if 'title' in kwargs:
        normalized_title = normalize_title(kwargs['title'])
        imdb_movies = imdb_cl.search_movie(kwargs['title'])

        for imdb_movie in imdb_movies:
            # Only take into account the movies whose release year
            # is not earlier than one year ago
            if imdb_movie.get('year') >= datetime.date.today().year - 1:

                # Get full info about the movie
                imdb_cl.update(imdb_movie)

                # Compose all known movie titles into a list
                titles = [imdb_movie.get('title')]
                if imdb_movie.get('akas'):
                    akas = [aka.split('::')[0] for aka in imdb_movie['akas']]
                    titles += akas
                if imdb_movie.get('akas from release info'):
                    akas_from_release_info = [aka.split('::')[1] for aka
                                              in imdb_movie['akas from release info']]
                    titles += akas_from_release_info

                # Traverse the titles list and see if anything matches the pk_title
                for title in titles:
                    normalized_imdb_title = normalize_title(title)
                    # Return IMDB movie object if there is a title match
                    if titles_match(normalized_title, normalized_imdb_title):
                        return (imdb_movie.getID(), imdb_movie.get('title'),
                                imdb_movie.get('rating'))
                else:
                    # Return None if there was no title match
                    return None
    elif 'id' in kwargs:
        # Find IMDB movie by id
        imdb_movie = imdb_cl.get_movie(kwargs['id'])
        return (imdb_movie.getID(), imdb_movie.get('title'),
                imdb_movie.get('rating'))


sched = BackgroundScheduler()

# Add two jobs: one for immediate fetching of data (on start)
# and another one hourly
sched.add_job(write_movie_data, args=(db,))
sched.add_job(write_movie_data, args=(db,), trigger='cron', hour=1)


if __name__ == '__main__':
    sched.start()
    while True:
        time.sleep(60)

import copy
import datetime
import logging as log
import re
import time
import unicodedata
import urllib2

import imdb
import xmltodict

from sqlalchemy import or_

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.restful import Api, Resource, fields, marshal, abort, reqparse

from apscheduler.schedulers.background import BackgroundScheduler


SQLALCHEMY_DATABASE_URI = \
    'mysql://clap_user:clap_user_pw@localhost/clap_db?unix_socket=/tmp/mysql.sock'


app = Flask(__name__)
api = Api(app)
app.config.from_object(__name__)
db = SQLAlchemy(app)
log.basicConfig(format='[%(asctime)s]: %(levelname)s: %(message)s', level=log.INFO)
sched = BackgroundScheduler()


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    show_start = db.Column(db.DateTime)
    show_end = db.Column(db.DateTime)
    url = db.Column(db.String(255))
    imdb_data = db.relationship('IMDBData', uselist=False)
    show_times = db.relationship('ShowTime')

    def __init__(self, id, title, show_start, show_end, url):
        self.id = id
        self.title = title
        self.show_start = show_start
        self.show_end = show_end
        self.url = url

    def __repr__(self):
        return '<PKMovie %r, %r>' % (self.id, self.title)


class IMDBData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    rating = db.Column(db.Float)
    pk_movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))

    def __init__(self, id, title, rating, pk_movie_id):
        self.id = id
        self.title = title
        self.rating = rating
        self.pk_movie_id = pk_movie_id

    def __repr__(self):
        return '<IMDBMovie %r, %r>' % (self.id, self.title)


class ShowTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime)
    hall_id = db.Column(db.Integer)
    technology = db.Column(db.String(8))
    order_url = db.Column(db.String(255))
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))

    def __init__(self, id, datetime, hall_id, technology, order_url, movie_id):
        self.id = id
        self.datetime = datetime
        self.hall_id = hall_id
        self.technology = technology
        self.order_url = order_url
        self.movie_id = movie_id

    def __repr__(self):
        return '<ShowTime %r, %r>' % (self.id, self.datetime)


imdb_data_fields = {
    'id': fields.Integer,
    'title': fields.String,
    'rating': fields.Float,
}


show_time_fields = {
    'id': fields.Integer,
    'datetime': fields.DateTime,
    'hall_id': fields.Integer,
    'technology': fields.String,
    'order_url': fields.String
}


movie_fields = {
    'id': fields.Integer,
    'title': fields.String,
    'show_start': fields.DateTime,
    'show_end': fields.DateTime,
    'url': fields.String,
}


class MovieListAPI(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('imdb_data', type=str)
        self.parser.add_argument('showtimes', type=str)
        super(MovieListAPI, self).__init__()

    def get(self):
        args = self.parser.parse_args()
        m_fields = copy.copy(movie_fields)

        if args['imdb_data']:
            m_fields['imdb_data'] = fields.Nested(imdb_data_fields)
        if args['showtimes']:
            m_fields['show_times'] = fields.Nested(show_time_fields)

        return {'movies': marshal(get_current_movies(), m_fields)}


class MovieAPI(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('imdb_data', type=str)
        self.parser.add_argument('showtimes', type=str)
        super(MovieAPI, self).__init__()

    def get(self, movie_id):
        movie = Movie.query.filter_by(id=movie_id).first()

        if not movie:
            abort(404, message='Movie {} not found'.format(movie_id))

        args = self.parser.parse_args()
        m_fields = copy.copy(movie_fields)

        if args['imdb_data']:
            m_fields['imdb_data'] = fields.Nested(imdb_data_fields)
        if args['showtimes']:
            m_fields['show_times'] = fields.Nested(show_time_fields)

        return {'movie': marshal(movie, m_fields)}


# class MovieIMDBDataAPI(Resource):
#     def get(self, movie_id):
#         movie = Movie.query.filter_by(id=movie_id).first()
#         if not movie:
#             abort(404, message='Movie {} not found'.format(movie_id))
#         imdb_data = movie.imdb_data
#         if imdb_data:
#             resp = {'imdb_data': marshal(imdb_data, imdb_data_fields)}
#         else:
#             resp = {'imdb_data': {}}
#
#         return resp
#
#
# class MovieShowTimesAPI(Resource):
#     def get(self, movie_id):
#         movie = Movie.query.filter_by(id=movie_id).first()
#         if not movie:
#             abort(404, message='Movie {} not found'.format(movie_id))
#         showtime_data = movie.show_times
#         if showtime_data:
#             resp = {'showtimes': marshal(showtime_data, show_time_fields)}
#         else:
#             resp = {'showtimes': []}
#
#         return resp


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


def get_current_movies(show_start_within_days=14):
    """
    Get list of PK movies that are currently being shown or will start to be shown
    in the nearest days

    :param show_start_within_days: number of days in future that movie show should
                                   start within
    :return: List of PK movie objects
    """
    today = datetime.date.today()
    show_start_last_day = today + datetime.timedelta(show_start_within_days)

    movies_list = Movie.query.filter(Movie.show_start != None) \
        .filter(Movie.show_start <= show_start_last_day) \
        .filter(or_(Movie.show_end == None, Movie.show_end >= today)).all()

    return movies_list


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


api.add_resource(MovieListAPI, '/movies')
api.add_resource(MovieAPI, '/movies/<int:movie_id>')
# api.add_resource(MovieIMDBDataAPI, '/movies/<int:movie_id>/imdb-data')
# api.add_resource(MovieShowTimesAPI, '/movies/<int:movie_id>/showtimes')


if __name__ == '__main__':
    db.create_all()

    # Add two jobs: one for immediate fetching of data (on start)
    # and another one hourly
    sched.add_job(write_movie_data, args=(db,))
    sched.add_job(write_movie_data, args=(db,), trigger='cron', hour=1)

    sched.start()

    # Disable reloader due to this issue http://stackoverflow.com/a/15491587/695332
    app.run(use_reloader=False)

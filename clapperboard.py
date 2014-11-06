import datetime
import logging
import re
import unicodedata
import urllib2

import imdb
import xmltodict

from os.path import abspath, dirname, join

from sqlalchemy import or_

from flask import Flask, render_template
from flask.ext.sqlalchemy import SQLAlchemy

from apscheduler.schedulers.background import BackgroundScheduler


_cwd = dirname(abspath(__file__))

DEBUG = True
SQLALCHEMY_DATABASE_URI = 'mysql://root@localhost/clapperboard'


app = Flask(__name__)
app.config.from_object(__name__)
db = SQLAlchemy(app)
logging.basicConfig()
sched = BackgroundScheduler()


class PKMovie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255))
    show_start = db.Column(db.Date)
    show_end = db.Column(db.Date)
    imdb = db.relationship('IMDBMovie', uselist=False)
    show_times = db.relationship('ShowTime')

    def __init__(self, id, url, show_start, show_end):
        self.id = id
        self.url = url
        self.show_start = show_start
        self.show_end = show_end

    def __repr__(self):
        return '<PKMovie %r, %r>' % (self.id, self.url)


class IMDBMovie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    rating = db.Column(db.Float)
    pk_movie_id = db.Column(db.Integer, db.ForeignKey('pk_movie.id'))

    def __init__(self, id, title, rating, pk_movie_id):
        self.id = id
        self.title = title
        self.rating = rating
        self.pk_movie_id = pk_movie_id

    def __repr__(self):
        return '<IMDBMovie %r, %r>' % (self.id, self.title)


class ShowTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    hall_id = db.Column(db.Integer)
    technology = db.Column(db.String(8))
    order_url = db.Column(db.String(255))
    pk_movie_id = db.Column(db.Integer, db.ForeignKey('pk_movie.id'))

    def __init__(self, date, time, hall_id, technology, order_url, pk_movie_id):
        self.date = date
        self.time = time
        self.hall_id = hall_id
        self.technology = technology
        self.order_url = order_url
        self.pk_movie_id = pk_movie_id

    def __repr__(self):
        return '<ShowTime %r %r>' % (self.date, self.pk_movie_id)


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


def string_to_datetime(str, type='date', remove_time=False):
    """
    Convert date string representation to datetime object

    :param str: Date string format
    :param type: What type does the string represent. 'date' and 'time' are accepted
    :param remove_time: Remove time from datetime object (leave date only)
    :return: Datetime object
    """
    if type == 'date':
        if remove_time:
            dt = datetime.datetime.strptime(str, '%Y-%m-%d %H:%M:%S').date() if str \
                else None
        else:
            dt = datetime.datetime.strptime(str, '%Y-%m-%d').date() if str else None
    elif type == 'time':
        dt = datetime.datetime.strptime(str, '%H:%M').time() if str else None

    return dt


def update_movie_imdb_data(movie):
    pass


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
    return PKMovie.query.outerjoin(IMDBMovie).filter(PKMovie.show_start != None) \
        .filter(PKMovie.show_start <= show_start_last_day) \
        .filter(or_(PKMovie.show_end == None, PKMovie.show_end >= today)) \
        .order_by(IMDBMovie.rating.desc()).all()


def get_showtimes_for_movie(showtimes_struct, movie_id):
    """
    Get list of showtimes for a specific PK movie.

    :param showtimes_struct: Dictionary with showtimes data
    :param movie_id: PK movie id
    :return: List of showtime objects
    """
    movie_show_times = []
    for show_time in showtimes_struct:
        for show in show_time['show']:
            if show['@movie-id'] == movie_id:
                if show['@order-url']:
                    show_time_date = string_to_datetime(show['@full-date'],
                                                        remove_time=True)
                    show_time_time = string_to_datetime(show['@time'],
                                                        type='time')
                    movie_show_times.append((show_time_date, show_time_time,
                                             show['@hall-id'], show['@technology'],
                                             show['@order-url'], movie_id))
    return movie_show_times


def write_pk_movie_data(db):
    """
    Create new of update existing movie record in database.

    :return:
    """
    data = get_pk_data('lvov')
    show_times = data['showtimes']['day']

    for movie in data['movies']['movie']:
        dt_start = string_to_datetime(movie['dt-start'])
        dt_end = string_to_datetime(movie['dt-end'])

        # See if the record with that id already exists
        record = PKMovie.query.filter_by(id=movie['@id']).first()

        if record:
            # If it does update its show start and end dates
            if record.show_start != dt_start:
                record.show_start = dt_start
            if record.show_end != dt_end:
                record.show_end = dt_end
            # See if it has IMDB data associated
            if record.imdb:
                # If it does update its rating
                imdb_movie = get_imdb_movie_data(imdb_id=record.imdb.id)
                if record.imdb.rating != imdb_movie.get('rating'):
                    record.imdb.rating = imdb_movie.get('rating')
                continue
            else:
                # If not get movie data from IMDB
                pk_title = extract_title_from_pk_url(record.url)
                imdb_movie = get_imdb_movie_data(pk_title=pk_title)
            if record.show_times:
                # TODO: Update showtimes in db if they changed in XML
                pass
            else:
                # If no show times for a movie found add them
                movie_show_times = get_showtimes_for_movie(show_times, record.id)
                for show_time in movie_show_times:
                    show_time_record = ShowTime(*show_time)
                    db.session.add(show_time_record)
        else:
            # If the record was not found create a new one
            pk_movie_record = PKMovie(movie['@id'], movie['@url'], dt_start, dt_end)
            db.session.add(pk_movie_record)

            # Set show times for the movie
            movie_show_times = get_showtimes_for_movie(show_times, movie['@id'])
            for show_time in movie_show_times:
                show_time_record = ShowTime(*show_time)
                db.session.add(show_time_record)

            # Set IMDB data for the movie
            pk_title = extract_title_from_pk_url(movie['@url'])
            imdb_movie = get_imdb_movie_data(pk_title=pk_title)
        if imdb_movie:
            imdb_movie_record = IMDBMovie(imdb_movie.getID(),
                                          imdb_movie.get('title'),
                                          imdb_movie.get('rating'),
                                          movie['@id'])
            db.session.add(imdb_movie_record)
        db.session.commit()


def fetch_pk_showtime_data():
    pass


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


def get_imdb_movie_data(**kwargs):
    """
    Retrieve IMDB info about a movie either by its PK title or by IMDB id

    :param kwargs: Either pk_title or imdb_id
    :return: IMDB movie object if found, None otherwise
    """
    imdb_cl = imdb.IMDb()
    if 'pk_title' in kwargs:
        normalized_pk_title = normalize_title(kwargs['pk_title'])
        imdb_movies = imdb_cl.search_movie(kwargs['pk_title'])

        for imdb_movie in imdb_movies:
            # Only take into account the movies whose release year
            # is not earlier than one year ago
            if imdb_movie.get('year') >= datetime.date.today().year - 1:

                # Get full info about the movie
                imdb_cl.update(imdb_movie)

                # Compose all known movie titles into a list
                titles = [imdb_movie['title']]
                if imdb_movie.get('akas'):
                    akas = [aka.split('::')[0] for aka in imdb_movie['akas']]
                    titles += akas
                if imdb_movie.get('akas from release info'):
                    akas_from_release_info = [aka.split('::')[1] for aka
                                              in
                                              imdb_movie['akas from release info']]
                    titles += akas_from_release_info

                # Traverse the titles list and see if anything matches the pk_title
                for title in titles:
                    normalized_imdb_title = normalize_title(title)
                    # Return IMDB movie object if there is a title match
                    if titles_match(normalized_pk_title, normalized_imdb_title):
                        return imdb_movie
                else:
                    # Return None if there was no title match
                    return None
    elif 'imdb_id' in kwargs:
        # Find IMDB movie by id
        return imdb_cl.get_movie(kwargs['imdb_id'])


@app.route("/")
def show_movies():
    movies = get_current_movies()
    return render_template('movies_list.html', movies=movies)


if __name__ == '__main__':
    db.create_all()

    # Add two jobs: one for immediate fetching of data (on start)
    # and another one hourly
    sched.add_job(write_pk_movie_data, args=(db,))
    sched.add_job(write_pk_movie_data, args=(db,), trigger='cron', hour=1)

    sched.start()

    # Disable reloader due to this issue http://stackoverflow.com/a/15491587/695332
    app.run(use_reloader=False)

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
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + join(_cwd, 'clapperboard.db')


app = Flask(__name__)
app.config.from_object(__name__)
db = SQLAlchemy(app)
logging.basicConfig()
sched = BackgroundScheduler()


class PKMovie(db.Model):
    id = db.Column(db.String, primary_key=True)
    url = db.Column(db.String)
    show_start = db.Column(db.Date)
    show_end = db.Column(db.Date)
    show_times = db.relationship('ShowTime', backref='pk_movie')
    imdb = db.relationship('IMDBMovie', backref='pk_movie', uselist=False)

    def __init__(self, id, url, show_start, show_end):
        self.id = id
        self.url = url
        self.show_start = show_start
        self.show_end = show_end

    def __repr__(self):
        return '<PKMovie %r, %r>' % (self.id, self.url)


class IMDBMovie(db.Model):
    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String)
    rating = db.Column(db.String)
    pk_id = db.Column(db.Integer, db.ForeignKey('pk_movie.id'))

    def __init__(self, id, title, rating, pk_id):
        self.id = id
        self.title = title
        self.rating = rating
        self.pk_id = pk_id

    def __repr__(self):
        return '<IMDBMovie %r, %r>' % (self.id, self.title)


class ShowTime(db.Model):
    id = db.Column(db.String, primary_key=True)
    date = db.Column(db.DateTime)
    time = db.Column(db.Time)
    hall_id = db.Column(db.String)
    technology = db.Column(db.String)
    order_url = db.Column(db.String)
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


def show_date_to_datetime(str):
    """
    Convert date string representation to datetime object

    :param str: Date string format
    :return: Datetime object
    """
    return datetime.datetime.strptime(str, '%Y-%m-%d').date() if str else None


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


def write_pk_movie_data(db):
    """
    Create new of update existing movie record in database.

    :return:
    """
    data = get_pk_data('lvov')

    for movie in data['movies']['movie']:
        dt_start = show_date_to_datetime(movie['dt-start'])
        dt_end = show_date_to_datetime(movie['dt-end'])

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
        else:
            # If the record was not found create a new one
            pk_movie_record = PKMovie(movie['@id'], movie['@url'], dt_start, dt_end)
            db.session.add(pk_movie_record)
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


# Add two jobs: one for immediate fetching of data (on start)
# and another one hourly
sched.add_job(write_pk_movie_data, args=(db,))
sched.add_job(write_pk_movie_data, args=(db,), trigger='cron', hour=1)


if __name__ == "__main__":
    db.create_all()
    sched.start()
    # Disable reloader due to this issue http://stackoverflow.com/a/15491587/695332
    app.run(use_reloader=False)

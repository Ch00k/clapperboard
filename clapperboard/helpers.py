import datetime
import re
import time
import urllib2

import imdb
import unicodedata
import xmltodict


def get_pk_data(xml_url):
    """
    Get movies and showtimes data from PK website.

    :return: Dictionary containing all PK movies and showtimes data
    """
    url = xml_url
    data = urllib2.urlopen(url).read()
    data_dict = xmltodict.parse(data)

    return data_dict['planeta-kino']


def extract_title_from_pk_url(url):
    return url.split('/')[-2].replace('-', ' ')


def datetime_string_to_timestamp(str):
    """
    Convert datetime string representation to timestamp

    :param str: Date string format
    :return: Integer
    """
    if str:
        # A dull check whether the string contains time
        pattern = '%Y-%m-%d %H:%M:%S' if ':' in str else '%Y-%m-%d'
        return time.mktime(datetime.datetime.strptime(str, pattern).timetuple())
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
                    show_ts = datetime_string_to_timestamp(show['@full-date'])
                    movie_show_times.append((int(show_time_id), show_ts,
                                             show['@hall-id'], show['@technology'],
                                             show['@order-url'], movie_id))
    return movie_show_times


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
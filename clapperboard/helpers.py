import datetime
import re
import time
import urllib2

import imdb
import unicodedata
import xmltodict


def get_pk_data():
    """
    Get movies and showtimes data from PK website.

    :return: Dictionary containing all PK movies and showtimes data
    """
    opener = urllib2.build_opener()
    # Tweak the server to think we are in neither of its known locations
    # (actually a bug on PK)
    opener.addheaders.append(('Cookie', 'gdc=london'))

    # Empty string is Kiev
    theatres = ['', 'kharkov', 'lvov', 'odessa', 'odessa2', 'sumy', 'yalta']

    movies = []
    showtimes = []
    seen_movies = set()

    order_url_pattern = \
        '^https:\/\/cabinet.planeta-kino.com.ua\/hall\/\?show_id=(\d+)&.*$'

    for theatre in theatres:
        url = 'http://planeta-kino.com.ua/{}/showtimes/xml/'.format(theatre)
        xml_data = opener.open(url).read()
        data_dict = xmltodict.parse(xml_data, dict_constructor=dict)
        location_data = data_dict['planeta-kino']
        movies_data = location_data['movies']['movie']
        showtimes_data = location_data['showtimes']['day']

        for pk_movie in movies_data:
            if pk_movie['@id'] not in seen_movies:
                movie = {
                    'id': int(pk_movie['@id']),
                    'ua_title': pk_movie['title'],
                    'url_title': pk_movie['@url'].split('/')[-2],
                    'show_start': datetime_string_to_timestamp(pk_movie['dt-start']),
                    'show_end': datetime_string_to_timestamp(pk_movie['dt-end']),
                }
                movies.append(movie)
                seen_movies.add(pk_movie['@id'])
        for day in showtimes_data:
            for pk_showtime in day['show']:
                if pk_showtime['@order-url']:
                    showtime = {
                        'id': int(re.match(order_url_pattern,
                                           pk_showtime['@order-url']).group(1)),
                        'theatre_id': pk_showtime['@theatre-id'].split('-')[-1],
                        'hall_id': int(pk_showtime['@hall-id']),
                        'date_time': datetime_string_to_timestamp(
                            pk_showtime['@full-date']),
                        'movie_id': int(pk_showtime['@movie-id']),
                        'technology': pk_showtime['@technology']
                    }
                    showtimes.append(showtime)

    for movie in movies:
        movie['showtimes'] = []
        for showtime in showtimes:
            if showtime['movie_id'] == movie['id']:
                movie['showtimes'].append(showtime)

    return movies


def datetime_string_to_timestamp(str):
    """
    Convert datetime string representation to timestamp

    :param str: Date string format
    :return: Integer
    """
    if str:
        # A dull check whether the string contains time
        pattern = '%Y-%m-%d %H:%M:%S' if ':' in str else '%Y-%m-%d'
        return int(time.mktime(datetime.datetime.strptime(str, pattern).timetuple()))
    else:
        return None


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
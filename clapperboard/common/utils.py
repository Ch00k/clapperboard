import datetime
import logging
import re
import rfc822

import imdb
import pytz
import requests
import unicodedata
import xmltodict

log = logging.getLogger(__name__)


LIST_SEPARATOR = ', '


def get_pk_data(theatres, force=False):
    """
    Get movies and showtimes data from PK website.

    :param: theatres: List of dictionaries with theatre url codes
                      and last fetched times
    :param: force: Forcefully get all data regardless of Last-Modified
                   header value
    :return: Tuple of lists (movies, showtimes, theatres)
    """

    # Make the server think we are in neither of its known locations
    # (actually a bug on PK)
    cookies = {'gdc': 'london'}

    movies = []
    showtimes = []
    seen_movies = set()

    order_url_pattern = \
        '^https:\/\/cabinet.planeta-kino.com.ua\/hall\/\?show_id=(\d+)&.*$'

    for theatre in theatres:
        url = ('http://planeta-kino.com.ua/{}/showtimes/xml/'
               .format(theatre['url_code']))
        try:
            log.info('Getting data for {}'.format(theatre['en_name']))
            resp = requests.get(url, cookies=cookies)
        except requests.ConnectionError as error:
            log.error(error)
            # TODO: a temporary workaround for
            # https://github.com/Ch00k/clapperboard/issues/4
            log.error('Could not fetch data for {}. '
                      'Skipping the whole run'.format(theatre['en_name']))
            return
        last_modified = _rfc822_string_to_utc_datetime(
            resp.headers['Last-Modified']
        )

        if not force:
            if (theatre['last_fetched'] and
                    theatre['last_fetched'] >= last_modified):
                continue

        xml_data = resp.text
        data_dict = xmltodict.parse(xml_data, dict_constructor=dict)
        location_data = data_dict['planeta-kino']
        movies_data = location_data['movies']['movie']
        showtimes_data = location_data['showtimes']['day']

        # TODO: There must be an option to avoid this in xmltodict
        if not isinstance(showtimes_data, list):
            showtimes_data = [showtimes_data]

        for pk_movie in movies_data:
            if pk_movie['@id'] not in seen_movies:
                movie = dict(
                    id=int(pk_movie['@id']),
                    title=pk_movie['title'],
                    url_code=pk_movie['@url'].split('/')[-2],
                    show_start=_string_to_utc_datetime(pk_movie['dt-start']),
                    show_end=_string_to_utc_datetime(pk_movie['dt-end'])
                )
                movies.append(movie)
                seen_movies.add(pk_movie['@id'])
        for day in showtimes_data:
            for pk_showtime in day['show']:
                if pk_showtime['@order-url']:
                    showtime = dict(
                        id=int(re.match(order_url_pattern,
                                        pk_showtime['@order-url']).group(1)),
                        theatre=pk_showtime['@theatre-id'],
                        hall_id=int(pk_showtime['@hall-id']),
                        technology=pk_showtime['@technology'],
                        date_time=_string_to_utc_datetime(
                            pk_showtime['@full-date']
                        ),
                        order_url=pk_showtime['@order-url'],
                        movie_id=int(pk_showtime['@movie-id'])
                    )
                    showtimes.append(showtime)

        theatre['last_fetched'] = last_modified

    return movies, showtimes, theatres


def get_movie_imdb_data(**kwargs):
    """
    Retrieve IMDB info about a movie either by its PK title or by IMDB id.

    :param kwargs: Either title or IMDB id
    :return: Dictionary with IMDB movie data
    """
    imdb_cl = imdb.IMDb()

    if 'title' in kwargs:
        normalized_title = _normalize_title(kwargs['title'])
        imdb_movies = imdb_cl.search_movie(kwargs['title'])

        for imdb_movie in imdb_movies:

            # We are only interested in movies (no series/episodes)
            if imdb_movie.get('kind') not in ('movie', 'video movie'):
                continue

            # Only take into account the movies whose release year
            # is not earlier than one year ago. If IMDB movie's year is
            # unknown assume it's the next year
            current_year = datetime.date.today().year
            if imdb_movie.get('year', current_year + 1) < current_year - 1:
                continue

            # Get full info about the movie
            imdb_cl.update(imdb_movie)

            # Compose all known movie titles into a list
            titles = [imdb_movie.get('title')]
            if imdb_movie.get('akas'):
                akas = [aka.split('::')[0] for aka in imdb_movie['akas']]
                titles += akas
            if imdb_movie.get('akas from release info'):
                akas_from_release_info = [
                    aka.split('::')[1] for
                    aka in imdb_movie['akas from release info']
                ]
                titles += akas_from_release_info

            # Traverse the titles list and see if anything matches the pk_title
            for title in titles:
                normalized_imdb_title = _normalize_title(title)
                # Return IMDB movie object if there is a title match
                if _titles_match(normalized_title, normalized_imdb_title):
                    return _compile_imdb_data_dict(imdb_movie)
        else:
            return {}

    elif 'id' in kwargs:
        # Find IMDB movie by id
        # TODO: Handle inexistent ID
        return _compile_imdb_data_dict(imdb_cl.get_movie(kwargs['id']))


def _string_to_utc_datetime(dt_string):
    """
    Convert date/time string representation to UTC datetime object
    (without tzinfo)

    :param dt_string: Date/time string format
    :return: datetime object
    """
    if dt_string:
        # A dull check whether the string contains time
        if ':' in dt_string:
            local_dt = datetime.datetime.strptime(dt_string,
                                                  '%Y-%m-%d %H:%M:%S')
            local_tz = pytz.timezone('Europe/Kiev')
            utc_tz = pytz.UTC
            return (utc_tz.normalize(local_tz.localize(local_dt))
                    .replace(tzinfo=None))
        else:
            return datetime.datetime.strptime(dt_string, '%Y-%m-%d').date()
    else:
        return None


def _rfc822_string_to_utc_datetime(rfc822_string):
    """
    Convert RFC 822 date/time string representation to UTC datetime object
    (without tzinfo)

    :param rfc822_string: Date/time string in RFC822 format
    :return: datetime object
    """
    return datetime.datetime.fromtimestamp(
        rfc822.mktime_tz(rfc822.parsedate_tz(rfc822_string)), pytz.UTC
    ).replace(tzinfo=None)


def _compile_imdb_data_dict(movie_obj):
    """
    Compile a dictionary with IMDB movie data out of an IMDBpy Movie object
    :param movie_obj: IMDBpy movie object
    :return: dictionary
    """
    imdb_data_dict = dict(
        id=int(movie_obj.getID()),
        title=movie_obj.get('title'),
        genre=LIST_SEPARATOR.join(movie_obj.get('genre')),
        country=LIST_SEPARATOR.join(movie_obj.get('country')),
        rating=movie_obj.get('rating')
    )

    imdb_data_dict['director'] = LIST_SEPARATOR.join(
        [director.get('name') for director in movie_obj.get('director')]
    )

    if movie_obj.get('cast'):
        imdb_data_dict['cast'] = LIST_SEPARATOR.join(
            [cast.get('name') for cast in movie_obj.get('cast')[:10]]
        )

    else:
        imdb_data_dict['cast'] = None

    runtime = movie_obj.get('runtime')
    if runtime:
        # https://github.com/alberanid/imdbpy/blob/master/imdb/parser/mobile/__init__.py#L411
        if '::(' in runtime[0]:
            runtime = runtime[0].split('::(')[0]
        else:
            runtime = runtime[0].split(':')[-1]
        imdb_data_dict['runtime'] = int(runtime)
    else:
        imdb_data_dict['runtime'] = None

    return imdb_data_dict


def _titles_match(pk_title, imdb_title):
    """
    Try to find a match between a PK title and an IMDB title.

    First triy a simple string equality, then add a 'the' to PK title,
    then remove 'the' from pk_title if it exists, then remove all 'and'
    occurrences from PK title.

    :param pk_title: Title retrieved from PK movie URL
    :param imdb_title: Title of the movie found on IMDB
    :return: True if titles match, False otherwise
    """
    return (
        (pk_title == imdb_title) or
        ('the' + pk_title == imdb_title) or
        (pk_title.startswith('the') and pk_title[3:] == imdb_title) or
        (pk_title.replace('and', '') == imdb_title)
    )


def _normalize_title(title):
    """
    Transform movie title so that it's ready for string comparison.

    Remove everything but alphanumeric chars from the string and
    replaces unicode characters with their ascii equivalents.

    :param title: Movie title
    :return: Normalized title
    """
    # Convert all unicode chars to ASCII
    ascii_title = unicodedata.normalize('NFKD', title).encode('ascii',
                                                              'ignore')

    # Remove all non-alnum chars
    pattern = re.compile('[\W_]+')
    normalized_title = pattern.sub('', ascii_title.lower())

    return normalized_title

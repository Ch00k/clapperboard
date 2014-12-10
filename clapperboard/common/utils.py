import datetime
import logging
import re
from email.utils import parsedate_tz, mktime_tz

import pytz
import requests
import xmltodict
from lxml import html as lh


log = logging.getLogger(__name__)

LIST_SEPARATOR = ', '


def get_pk_data(theatres, force):
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

    order_url_pattern = ("^https:\/\/cabinet.planeta-kino.com.ua"
                         "\/hall\/\?show_id=(\d+)&.*$")

    for theatre in theatres:
        url = ("http://planeta-kino.com.ua/{}/showtimes/xml/"
               .format(theatre['url_code']))
        try:
            log.info("Getting data for {}".format(theatre['en_name']))
            resp = requests.get(url, cookies=cookies)
        except requests.ConnectionError as error:
            log.error(error)
            # TODO: a temporary workaround for
            # https://github.com/Ch00k/clapperboard/issues/4
            raise RuntimeError(
                "Could not fetch data for {}. Skipping the whole run".format(
                    theatre['en_name'])
            )

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
            if 'show' not in day:
                continue
            # TODO: There must be an option to avoid this in xmltodict
            if not isinstance(day['show'], list):
                day['show'] = [day['show']]
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
    # XPath selectors on movie search page (/find)
    link_xpath = (
        "//div[@class='findSection']/table[@class='findList']"
        "/tr[starts-with(@class, 'findResult')][1]/td[@class='result_text']"
        "/a/@href"
    )

    # XPath selectors on movie page (/title/tt<id>)
    title_xpath = "//td[@id='overview-top']/h1/span[@itemprop='name']/text()"
    rating_xpath = "//div[@class='titlePageSprite star-box-giga-star']/text()"
    genre_xpath = "//div[@itemprop='genre']/a/text()"
    director_xpath = "//div[@itemprop='director']/a/span/text()"
    cast_xpath = (
        "//table[@class='cast_list']/tr[position() >= 2 and position() <= 11]"
        "/td[@itemtype='http://schema.org/Person']/a/span/text()"
    )
    movie_details_box = "//div[@id='titleDetails']/div"
    runtime_xpath = "{}/time/text()".format(movie_details_box)
    country_xpath = "{}/h4[text()='Country:']/../a/text()".format(
        movie_details_box
    )

    base_url = "http://www.imdb.com"
    movie_url = "{}/title/tt{}"
    search_query_string = "find?q={}&&s=tt&&ttype=ft"
    headers = {'Accept-Language': 'en-US,en'}

    if 'title' in kwargs:
        search_resuls = requests.get(
            "{}/{}".format(
                base_url,
                search_query_string.format(kwargs['title'])
            ),
            headers=headers
        )

        lh_doc = lh.fromstring(search_resuls.text)
        movie_link = lh_doc.xpath(link_xpath)
        if movie_link:
            movie_link = movie_link[0]
        else:
            return {}

        pattern = "^\/title\/tt(\d+)\/\?ref_=fn_ft_tt_1$"
        movie_id = re.match(pattern, movie_link).group(1)
        movie_id = int(movie_id)

    elif 'id' in kwargs:
        movie_id = kwargs['id']
    else:
        raise RuntimeError(
            "Must be called with either IMDB movie ID of movie title"
        )

    movie_page = requests.get(
        movie_url.format(base_url, movie_id),
        headers=headers
    )

    lh_doc = lh.fromstring(movie_page.text)

    # Get all IMDB data
    title = lh_doc.xpath(title_xpath)
    rating = lh_doc.xpath(rating_xpath)
    genre = lh_doc.xpath(genre_xpath)
    director = lh_doc.xpath(director_xpath)
    cast = lh_doc.xpath(cast_xpath)
    country = lh_doc.xpath(country_xpath)
    runtime = lh_doc.xpath(runtime_xpath)

    # Normalize
    title = title[0]
    rating = float(rating[0].strip()) if rating else None
    genre = LIST_SEPARATOR.join([g.strip() for g in genre])
    director = LIST_SEPARATOR.join(director)
    cast = LIST_SEPARATOR.join(cast)
    country = LIST_SEPARATOR.join(country)
    runtime = int(runtime[0].split(' ')[0]) if runtime else None

    return dict(
        id=movie_id,
        title=title,
        rating=rating,
        genre=genre,
        country=country,
        director=director,
        cast=cast,
        runtime=runtime
    )


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
        mktime_tz(parsedate_tz(rfc822_string)),
        pytz.UTC
    ).replace(tzinfo=None)


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

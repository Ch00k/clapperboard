.. image:: https://travis-ci.org/Ch00k/clapperboard.svg?branch=develop
    :target: https://travis-ci.org/Ch00k/clapperboard

Clapperboard exposes the movies data of `Planeta Kino <http://planeta-kino.com.ua/lvov/>`_ cinemas in Ukraine as a RESTful API. In addition to getting the data Planeta Kino has publicly it also gets movies information from external sources like IMDB etc.

Built with `Flask <http://flask.pocoo.org/>`_, `Flask-RESTful <http://flask-restful.readthedocs.org/en/latest/>`_ `Flask-SQLAlchemy <https://pythonhosted.org/Flask-SQLAlchemy/>`_.

Gets movies data from `showtimes XMLs <http://planeta-kino.com.ua/i/showtimes/>`_

Uses `lxml <http://lxml.de/>`_ to scrape movies data from `IMDB <http://imdb.com/>`_

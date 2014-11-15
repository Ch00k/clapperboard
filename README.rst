Current functionality is very simple: get the list of currently running `Planeta Kino <http://planeta-kino.com.ua/lvov/>`_ movies and sort them by IMDB rating.

Built with `Flask <http://flask.pocoo.org/>`_, `Flask-RESTful <http://flask-restful.readthedocs.org/en/latest/>`_ `Flask-SQLAlchemy <https://pythonhosted.org/Flask-SQLAlchemy/>`_.

Gets PK data from a `showtimes XML <http://planeta-kino.com.ua/lvov/ua/showtimes/xml/>`_ (currently supports Lviv city only).

Uses `IMDbPY <http://imdbpy.sourceforge.net/>`_ to get IMDB data for a movie.

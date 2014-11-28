from flask.ext.sqlalchemy import SQLAlchemy

from clapperboard import app


db = SQLAlchemy(app)

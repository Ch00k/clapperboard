from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.migrate import Migrate


db = SQLAlchemy()
migrate = Migrate()

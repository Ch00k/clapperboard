from flask import Flask

from clapperboard.models import db, migrate
from clapperboard.resources import api, cors
from clapperboard.workers import celery


def create_apps():
    app = Flask(__name__)

    app.config.from_object('clapperboard.config')
    app.config.from_envvar('CLPBRD_CONFIG', silent=True)

    db.init_app(app)
    migrate.init_app(app, db)
    api.init_app(app)
    cors.init_app(app)
    celery.init_app(app)

    return app, celery


flask_app, celery_app = create_apps()

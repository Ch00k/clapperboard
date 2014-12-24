from flask import Flask

from clapperboard.models import db, migrate
from clapperboard.resources import api, anon_api, jwt, cors
from clapperboard.workers import celery
from clapperboard.tracker import tracker
from clapperboard.mailer import mailer


def create_apps():
    app = Flask(__name__)

    app.config.from_object('clapperboard.config')
    app.config.from_envvar('CLPBRD_CONFIG', silent=True)

    db.init_app(app)
    migrate.init_app(app, db)
    api.init_app(app)
    anon_api.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)
    celery.init_app(app)
    tracker.init_app(app)
    mailer.init_app(app)

    return app, celery


flask_app, celery_app = create_apps()

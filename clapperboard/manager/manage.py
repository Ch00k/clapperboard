# -*- coding: utf-8 -*-


from flask.ext.migrate import MigrateCommand

from sqlalchemy.exc import IntegrityError

from clapperboard import flask_app, celery_app
from clapperboard import models

from clapperboard.manager import manager
from clapperboard.models import db
from clapperboard.models.last_fetched import LastFetched
from clapperboard.models.technology import Technology
from clapperboard.models.theatre import Theatre

from clapperboard.workers.tasks import write_movie_data


manager.add_command('db', MigrateCommand)


# TODO: Find out how to do that with MigrateCommand
@manager.command
def db_seed():
    """
    Insert initial data into the database.
    """
    technologies = [
        (1, '2d', '2D'),
        (2, '3d', '3D'),
        (3, 'imax', 'IMAX'),
        (4, 'imax-3d', 'IMAX 3D'),
        (5, '4dx', '4DX')
    ]

    theatres = [
        (1, u'Київ', 'Kyiv', '', 'imax-kiev'),
        (2, u'Харків', 'Kharkiv', 'kharkov', 'pk-kharkov'),
        (3, u'Львів', 'Lviv', 'lvov', 'pk-lvov'),
        (4, u'Одеса (Таїрова)', 'Odesa (Tairova)', 'odessa', 'pk-odessa'),
        (5, u'Одеса (Котовського)', 'Odesa (Kotovskoho)', 'odessa2', 'pk-odessa2'),
        (6, u'Суми', 'Sumy', 'sumy', 'pk-sumy'),
        (7, u'Ялта', 'Yalta', 'yalta', 'pk-yalta')
    ]

    last_fetched = [
        (i, None, i) for i in range(1, 8)
    ]

    db.session.add_all([Technology(*tech) for tech in technologies])
    db.session.add_all([Theatre(*theatre) for theatre in theatres])
    db.session.add_all([LastFetched(*lf) for lf in last_fetched])

    # TODO find a better way to do seed idempotently
    try:
        db.session.commit()
    except IntegrityError as e:
        raise StandardError(e.message + '\r\nPerhaps database has already been seeded')


@manager.command
def fetch(force=False):
    """
    Run celery task forcefully to populate the database.
    :param: force: Forcefully get all data regardless of Last-Modified header value
    """
    write_movie_data.s(force=force).apply_async(queue='fetch_pk_data',
                                                routing_key='fetch_pk_data')


@manager.shell
def _make_context():
    return dict(app=flask_app, db=db, models=models, celery=celery_app)


def main():
    manager.run()


if __name__ == '__main__':
    main()

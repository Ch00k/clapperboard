# -*- coding: utf-8 -*-

import os

from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand

from sqlalchemy.exc import IntegrityError

from clapperboard import app
from clapperboard.models import db
# TODO: try using lambdas instead of this
from clapperboard.models.show_time import ShowTime
from clapperboard.models.last_fetched import LastFetched
from clapperboard.models.technology import Technology
from clapperboard.models.theatre import Theatre

from clapperboard.workers.tasks import write_movie_data


app.config.from_object('clapperboard.config.api')
if os.environ.get('CB_API_SETTINGS'):
    app.config.from_envvar('CB_API_SETTINGS')

migrate = Migrate(app, db)
manager = Manager(app)
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
def fetch():
    """
    Run celery task forcefully to populate the database.
    """
    write_movie_data.apply_async(queue='fetch_pk_data',
                                 routing_key='fetch_pk_data')


def main():
    manager.run()


if __name__ == '__main__':
    main()

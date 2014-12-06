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
        ('2d', '2D'),
        ('3d', '3D'),
        ('imax', 'IMAX'),
        ('imax-3d', 'IMAX 3D'),
        ('4dx', '4DX')
    ]

    theatres = [
        (u'Київ', 'Kyiv', '', 'imax-kiev'),
        (u'Харків', 'Kharkiv', 'kharkov', 'pk-kharkov'),
        (u'Львів', 'Lviv', 'lvov', 'pk-lvov'),
        (u'Одеса (Таїрова)', 'Odesa (Tairova)', 'odessa', 'pk-odessa'),
        (u'Одеса (Котовського)', 'Odesa (Kotovskoho)', 'odessa2',
         'pk-odessa2'),
        (u'Суми', 'Sumy', 'sumy', 'pk-sumy'),
        (u'Ялта', 'Yalta', 'yalta', 'pk-yalta')
    ]

    db.session.add_all([Technology(*tech) for tech in technologies])
    db.session.add_all([Theatre(*theatre) for theatre in theatres])

    last_fetched = [
        (None, i) for i in range(1, len(theatres) + 1)
    ]

    db.session.add_all([LastFetched(*lf) for lf in last_fetched])

    # TODO find a better way to do seed idempotently
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        raise StandardError(e.message +
                            '\nPerhaps database has already been seeded')


@manager.command
def fetch():
    """
    Run celery task forcefully to populate the database.
    """
    write_movie_data.s(
        not flask_app.config['RELY_ON_LAST_MODIFIED']
    ).apply_async(queue='fetch_pk_data', routing_key='fetch_pk_data')


@manager.shell
def _make_context():
    return dict(app=flask_app, db=db, models=models, celery=celery_app)


def main():
    manager.run()


if __name__ == '__main__':
    main()

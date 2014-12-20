from flask.ext.migrate import MigrateCommand

from clapperboard import flask_app, celery_app
from clapperboard import models

from clapperboard.manager import manager
from clapperboard.models import db
from clapperboard.workers.tasks import write_movie_data


manager.add_command('db', MigrateCommand)


@manager.command
def fetch():
    """
    Run celery task forcefully to populate the database.
    """
    write_movie_data.s(
        not flask_app.config['RELY_ON_LAST_MODIFIED']
    ).apply_async(
        queue='fetch_pk_data',
        routing_key='fetch_pk_data'
    )


@manager.shell
def _make_context():
    return dict(app=flask_app, db=db, models=models, celery=celery_app)


def main():
    manager.run()


if __name__ == '__main__':
    main()

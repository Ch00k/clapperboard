import os

from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand

from api import app, db


app.config.from_object('clapperboard.config.api')
if os.environ.get('CB_API_SETTINGS'):
    app.config.from_envvar('CB_API_SETTINGS')

migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)


def main():
    manager.run()


if __name__ == '__main__':
    main()

from celery.schedules import crontab
from kombu import Exchange, Queue


SQLALCHEMY_DATABASE_URI = ('mysql+pymysql://clap_user:clap_user_pw@localhost/'
                           'clap_db_v2?unix_socket=/tmp/mysql.sock')
CORS_HEADERS = 'Content-Type'
CORS_RESOURCES = {r'/*': {'origins': '*'}}
AUTH_TOKEN = '123qwe'
DEBUG = True
SQLALCHEMY_ECHO = False

RELY_ON_LAST_MODIFIED = False

BROKER_URL = 'amqp://'
CELERY_RESULT_BACKEND = 'amqp://'

CELERY_IGNORE_RESULT = True
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

CELERY_IMPORTS = ['clapperboard.workers.tasks']

CELERY_TASK_RESULT_EXPIRES = 3600

PK_FETCH_FREQUENCY_MINUTES = 30
CELERYBEAT_SCHEDULE = {
    'pk_fetch_periodic': {
        'task': 'clapperboard.workers.tasks.write_movie_data',
        'args': (not RELY_ON_LAST_MODIFIED,),
        'schedule': crontab(minute='*/{}'.format(PK_FETCH_FREQUENCY_MINUTES)),
        'options': {
            'queue': 'fetch_pk_data',
            'exchange': 'fetch_pk_data'
        }
    }
}

CELERY_QUEUES = (
    Queue(name='fetch_pk_data',
          exchange=Exchange('fetch_pk_data'),
          routing_key='fetch_pk_data'),
)

CELERY_ROUTES = {
    'clapperboard.workers.tasks.write_movie_data': {
        'queue': 'fetch_pk_data',
        'routing_key': 'fetch_pk_data'
    }
}

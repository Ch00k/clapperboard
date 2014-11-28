# from celery.schedules import crontab
# from kombu import Exchange, Queue
#
#
# BROKER_URL = 'amqp://'
# CELERY_RESULT_BACKEND = 'amqp://'
#
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_ACCEPT_CONTENT = ['json']
#
# CELERY_IMPORTS = ['clapperboard.workers.tasks']
#
# CELERY_TASK_RESULT_EXPIRES = 3600
#
# PK_FETCH_FREQUENCY_MINUTES = 30
# CELERYBEAT_SCHEDULE = {
#     'pk_fetch_periodic': {
#         'task': 'clapperboard.workers.tasks.write_movie_data',
#         'schedule': crontab(minute='*/{}'.format(PK_FETCH_FREQUENCY_MINUTES)),
#         'options': {
#             'queue': 'fetch_pk_data',
#             'exchange': 'fetch_pk_data'
#         }
#     }
# }
#
# CELERY_QUEUES = (
#     Queue(name='fetch_pk_data',
#           exchange=Exchange('fetch_pk_data'),
#           routing_key='fetch_pk_data'),
# )
#
# CELERY_ROUTES = {
#     'clapperboard.workers.tasks.write_movie_data': {
#         'queue': 'fetch_pk_data',
#         'routing_key': 'fetch_pk_data'
#     }
# }

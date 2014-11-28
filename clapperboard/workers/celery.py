from __future__ import absolute_import

from celery import Celery


# app = Celery('clapperboard')
# app.config_from_object('clapperboard.config.workers')
#
#
# if __name__ == '__main__':
#     app.start()


def make_celery(app):
    celery = Celery(app.import_name)
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

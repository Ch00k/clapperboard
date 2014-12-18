from __future__ import absolute_import

import flask
from celery import Celery
import rollbar


class FlaskCelery(Celery):
    def __init__(self, *args, **kwargs):

        super(FlaskCelery, self).__init__(*args, **kwargs)
        self.patch_task()
        self.tracker = rollbar

        if 'app' in kwargs:
            self.init_app(kwargs['app'])

    def patch_task(self):
        TaskBase = self.Task
        _celery = self

        class ContextTask(TaskBase):
            abstract = True

            def __call__(self, *args, **kwargs):
                if flask.has_app_context():
                    return TaskBase.__call__(self, *args, **kwargs)
                else:
                    with _celery.app.app_context():
                        return TaskBase.__call__(self, *args, **kwargs)

            def on_failure(self, exc, task_id, args, kwargs, einfo):
                _celery.tracker.report_exc_info()

        self.Task = ContextTask

    def init_app(self, app):
        self.app = app
        self.config_from_object(app.config)
        # TODO: There should be a better way to initialize rollbar app-wide
        self.tracker.init(self.conf.ROLLBAR_TOKEN, self.conf.ENVIRONMENT)

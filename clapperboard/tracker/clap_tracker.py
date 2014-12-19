import os

import rollbar
from rollbar.contrib.flask import report_exception

from flask import got_request_exception


class ClapTracker(object):
    def __init__(self):
        self.tracker = rollbar

    def init_app(self, app):
        self.tracker.init(
            app.config['ROLLBAR_TOKEN'],
            app.config['ENVIRONMENT'],
            root=os.path.dirname(os.path.realpath(__file__)),
            allow_logging_basic_config=False
        )
        got_request_exception.connect(report_exception, app)

from __future__ import absolute_import

from celery import Celery


app = Celery('clapperboard')
app.config_from_object('clapperboard.config.workers')


if __name__ == '__main__':
    app.start()

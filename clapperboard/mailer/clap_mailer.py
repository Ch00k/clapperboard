import requests


class ClapMailer(object):
    app = None
    mailgun_api = None

    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.mailgun_api = MailgunClient(
            app.config['MAILGUN_DOMAIN'],
            app.config['MAILGUN_API_KEY']
        )
        self.app = app

    def send_email(self, **kwargs):
        if not self.mailgun_api:
            raise ValueError('A valid app instance has not been provided')

        default_from = self.app.config.get('MAILGUN_DEFAULT_FROM')
        if default_from:
            kwargs.setdefault('from', default_from)
        return self.mailgun_api.send_email(**kwargs)


class MailgunClient(object):
    def __init__(self, domain, api_key):
        self.domain = domain
        self.api_key = api_key

    def send_email(self, **kwargs):
        response = requests.post(self.endpoint, data=kwargs, auth=self.auth)
        response.raise_for_status()
        return response

    @property
    def endpoint(self):
        return 'https://api.mailgun.net/v2/{}/messages'.format(self.domain)

    @property
    def auth(self):
        return 'api', self.api_key


# https://github.com/sleekslush/flask-mailgun/blob/master/flask_mailgun.py

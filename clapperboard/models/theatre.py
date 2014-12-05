from clapperboard.models import db
from clapperboard.models.common.utils import ClapQuery


class Theatre(db.Model):
    query_class = ClapQuery

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255))
    en_name = db.Column(db.String(255))
    url_code = db.Column(db.String(255), unique=True)
    st_url_code = db.Column(db.String(255))
    show_times = db.relationship('ShowTime', backref='theatre', lazy='dynamic')
    last_fetched = db.relationship('LastFetched', backref='theatre',
                                   uselist=False)

    def __init__(self, name, en_name, url_code, st_url_code):
        self.name = name
        self.en_name = en_name
        self.url_code = url_code
        self.st_url_code = st_url_code

    def __repr__(self):
        return '<Theatre %r>' % self.id

from clapperboard.models import db
from clapperboard.models.common.utils import ClapQuery


class Movie(db.Model):
    query_class = ClapQuery

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    title = db.Column(db.String(255))
    url_code = db.Column(db.String(255))
    show_start = db.Column(db.Date)
    show_end = db.Column(db.Date)
    imdb_id = db.Column(db.Integer, db.ForeignKey('imdb_data.id'))
    show_times = db.relationship('ShowTime', backref='movie', lazy='dynamic')

    def __init__(self, id, title, url_code, show_start, show_end):
        self.id = id
        self.title = title
        self.url_code = url_code
        self.show_start = show_start
        self.show_end = show_end

    def __repr__(self):
        return '<Movie %r>' % self.id

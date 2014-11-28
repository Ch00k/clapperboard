from clapperboard.models import db
from clapperboard.models.common.utils import ClapQuery


class LastFetched(db.Model):
    query_class = ClapQuery

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_time = db.Column(db.DateTime)
    theatre_id = db.Column(db.Integer, db.ForeignKey('theatre.id'))

    def __init__(self, id, date_time, theatre_id):
        self.id = id
        self.date_time = date_time
        self.theatre_id = theatre_id

    def __repr__(self):
        return '<FetchHistory %r>' % self.id

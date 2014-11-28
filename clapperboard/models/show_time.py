from clapperboard.models import db
from clapperboard.models.common.utils import ClapQuery


class ShowTime(db.Model):
    query_class = ClapQuery

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    theatre_id = db.Column(db.Integer, db.ForeignKey('theatre.id'))
    hall_id = db.Column(db.Integer)
    technology_id = db.Column(db.Integer, db.ForeignKey('technology.id'))
    date_time = db.Column(db.DateTime)
    order_url = db.Column(db.String(255))
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))

    def __init__(self, id, theatre_id, hall_id, technology_id, date_time, order_url,
                 movie_id):
        self.id = id
        self.theatre_id = theatre_id
        self.hall_id = hall_id
        self.technology_id = technology_id
        self.date_time = date_time
        self.order_url = order_url
        self.movie_id = movie_id

    def __repr__(self):
        return '<ShowTime %r>' % self.id

from clapperboard.models import db
from clapperboard.models.common.utils import ClapQuery


class Technology(db.Model):
    query_class = ClapQuery

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(255))
    name = db.Column(db.String(255))
    show_times = db.relationship('ShowTime', backref='technology',
                                 lazy='dynamic')

    def __init__(self, id, code, name):
        self.id = id
        self.code = code
        self.name = name

    def __repr__(self):
        return '<Technology %r>' % self.id

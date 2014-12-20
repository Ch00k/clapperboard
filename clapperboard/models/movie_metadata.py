from clapperboard.models import db
from clapperboard.models.common.utils import ClapQuery


class MovieMetadata(db.Model):
    query_class = ClapQuery

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    meta = db.Column(db.String(4096))
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))

    def __init__(self, meta, movie_id):
        self.meta = meta
        self.movie_id = movie_id

    def __repr__(self):
        return '<MovieMetadata %r>' % self.id

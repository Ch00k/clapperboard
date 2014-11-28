from clapperboard.models import db
from clapperboard.models.common.utils import ClapQuery


class IMDBData(db.Model):
    query_class = ClapQuery

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    title = db.Column(db.String(255))
    genre = db.Column(db.String(255))
    country = db.Column(db.String(255))
    director = db.Column(db.String(255))
    cast = db.Column(db.String(4096))
    runtime = db.Column(db.Integer)
    rating = db.Column(db.Float)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))

    def __init__(self, id, title, genre, country, director, cast, runtime, rating,
                 movie_id):
        self.id = id
        self.title = title
        self.genre = genre
        self.country = country
        self.director = director
        self.cast = cast
        self.runtime = runtime
        self.rating = rating
        self.movie_id = movie_id

    def __repr__(self):
        return '<IMDBData %r>' % self.id

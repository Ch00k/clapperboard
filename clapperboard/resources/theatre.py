from flask.ext.restful import Resource

from clapperboard.resources.common.schemas import TheatreSchema
from clapperboard.models.theatre import Theatre
from clapperboard.models.last_fetched import LastFetched
from clapperboard.resources.common.errors import THEATRE_NOT_FOUND


class TheatreListAPI(Resource):
    def __init__(self):
        super(TheatreListAPI, self).__init__()
        self.theatre_schema = TheatreSchema(many=True)

    def get(self):
        theatres = Theatre.query.all()
        res = self.theatre_schema.dump(theatres)
        return res.data


class TheatreAPI(Resource):
    def __init__(self):
        super(TheatreAPI, self).__init__()
        self.theatre_schema = TheatreSchema()

    def get(self, theatre_id):
        theatre = Theatre.query.get_or_abort(
            theatre_id, error_msg=THEATRE_NOT_FOUND.format(theatre_id)
        )
        res = self.theatre_schema.dump(theatre)
        return res.data

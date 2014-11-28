from flask.ext.restful import Resource, marshal

from clapperboard.resources.common.response_fields import THEATRE
from clapperboard.models.theatre import Theatre
from clapperboard.resources.common.errors import THEATRE_NOT_FOUND


class TheatreListAPI(Resource):
    def __init__(self):
        super(TheatreListAPI, self).__init__()

    def get(self):
        theatres = Theatre.query.all()
        return {'theatres': marshal(theatres, THEATRE)}


class TheatreAPI(Resource):
    def __init__(self):
        super(TheatreAPI, self).__init__()

    def get(self, theatre_id):
        theatre = Theatre.query.get_or_abort(theatre_id,
                                             error_msg=THEATRE_NOT_FOUND
                                             .format(theatre_id))
        return {'theatre': marshal(theatre, THEATRE)}

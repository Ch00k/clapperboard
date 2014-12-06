from flask.ext.restful import Resource

from clapperboard.resources.common.schemas import ShowTimeSchema
from clapperboard.models.show_time import ShowTime
from clapperboard.resources.common.errors import SHOWTIME_NOT_FOUND


class ShowTimesListAPI(Resource):
    def __init__(self):
        super(ShowTimesListAPI, self).__init__()
        self.showtime_schema = ShowTimeSchema(many=True)

    def get(self):
        show_times = ShowTime.query.all()
        res = self.showtime_schema.dump(show_times)
        return res.data


class ShowTimeAPI(Resource):
    def __init__(self):
        super(ShowTimeAPI, self).__init__()
        self.showtime_schema = ShowTimeSchema()

    def get(self, showtime_id):
        show_time = ShowTime.query.get_or_abort(
            showtime_id, error_msg=SHOWTIME_NOT_FOUND.format(showtime_id)
        )
        res = self.showtime_schema.dump(show_time)
        return res.data

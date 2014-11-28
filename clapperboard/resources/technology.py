from flask.ext.restful import Resource, marshal

from clapperboard.resources.common.response_fields import TECHNOLOGY
from clapperboard.models.technology import Technology
from clapperboard.resources.common.errors import TECHNOLOGY_NOT_FOUND


class TechnologyListAPI(Resource):
    def __init__(self):
        super(TechnologyListAPI, self).__init__()

    def get(self):
        technologies = Technology.query.all()
        return {'technologies': marshal(technologies, TECHNOLOGY)}


class TechnologyAPI(Resource):
    def __init__(self):
        super(TechnologyAPI, self).__init__()

    def get(self, technology_id):
        technology = Technology.query.get_or_abort(technology_id,
                                                   error_msg=TECHNOLOGY_NOT_FOUND
                                                   .format(technology_id))
        return {'technology': marshal(technology, TECHNOLOGY)}

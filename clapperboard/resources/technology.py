from flask.ext.restful import Resource, marshal

from clapperboard.resources.common.schemas import TechnologySchema
from clapperboard.models.technology import Technology
from clapperboard.resources.common.errors import TECHNOLOGY_NOT_FOUND


class TechnologyListAPI(Resource):
    def __init__(self):
        super(TechnologyListAPI, self).__init__()
        self.technology_schema = TechnologySchema(many=True)

    def get(self):
        technologies = Technology.query.all()
        res = self.technology_schema.dump(technologies)
        return res.data


class TechnologyAPI(Resource):
    def __init__(self):
        super(TechnologyAPI, self).__init__()
        self.technology_schema = TechnologySchema()

    def get(self, technology_id):
        technology = Technology.query.get_or_abort(
            technology_id, error_msg=TECHNOLOGY_NOT_FOUND.format(technology_id)
        )
        res = self.technology_schema.dump(technology)
        return res.data

from marshmallow import Schema, SchemaOpts, fields


class NamespaceOpts(SchemaOpts):
    """Same as the default class Meta options, but adds "name" and
    "plural_name" options for namespacing.
    """

    def __init__(self, meta):
        SchemaOpts.__init__(self, meta)
        self.name = getattr(meta, 'name', None)
        self.plural_name = getattr(meta, 'plural_name', self.name + 's')


class NamespacedSchema(Schema):
    OPTIONS_CLASS = NamespaceOpts

    def _postprocess(self, data, many, obj):
        """Execute any postprocessing steps, including adding a namespace
        to the final output.
        """
        data = Schema._postprocess(self, data, many, obj)
        if self.opts.name:   # Add namespace
            namespace = self.opts.name
            if self.many:
                namespace = self.opts.plural_name
            data = {namespace: data}
        return data


class MovieSchema(NamespacedSchema):
    class Meta:
        name = 'movie'

    id = fields.Integer()
    title = fields.String()
    url_code = fields.String()
    show_start = fields.String(default=None)
    show_end = fields.String(default=None)


class IMDBDataSchema(NamespacedSchema):
    class Meta:
        name = 'imdb_data'

    id = fields.Integer(default=None)
    title = fields.String()
    genre = fields.String()
    country = fields.String()
    director = fields.String()
    cast = fields.String()
    runtime = fields.Integer(default=None)
    rating = fields.Float(default=None)


class ShowTimeSchema(NamespacedSchema):
    class Meta:
        name = 'showtime'

    id = fields.Integer()
    theatre_id = fields.Integer()
    hall_id = fields.Integer()
    technology_id = fields.Integer()
    date_time = fields.DateTime()
    order_url = fields.Url()


class TheatreSchema(NamespacedSchema):
    class Meta:
        name = 'theatre'

    id = fields.Integer()
    name = fields.String()
    en_name = fields.String()
    url_code = fields.String()
    st_url_code = fields.String()


class TechnologySchema(NamespacedSchema):
    class Meta:
        name = 'technology'
        plural_name = 'technologies'

    id = fields.Integer()
    code = fields.String()
    name = fields.String()


class UserSchema(NamespacedSchema):
    class Meta:
        name = 'user'

    id = fields.Integer()
    username = fields.String()
    email = fields.Email()
    password = fields.String()

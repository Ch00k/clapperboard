from flask.ext.sqlalchemy import BaseQuery

from flask.ext.restful import abort


class ClapQuery(BaseQuery):
    def get_or_abort(self, ident, error_code=404, error_msg=None):
        """
        Like BaseQuery.get_or_404 but allows custom error code and message.
        """
        rv = self.get(ident)
        if rv is None:
            abort(error_code, code=error_code, message=error_msg)
        return rv

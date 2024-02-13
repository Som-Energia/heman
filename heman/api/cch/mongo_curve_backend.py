from heman.config import mongo
from pymongo import ASCENDING, DESCENDING

from .datetimeutils import as_naive


class MongoCurveBackend:
    def __init__(self, mongodb=None):
        self._mongodb = mongodb or mongo.db

    def get_cursor_db(self, collection, query):
        return self._mongodb[collection].aggregate(
            query
        )['result']

    def build_query(
        self,
        start=None,
        end=None,
        cups=None,
        **extra_filter
    ):

        match_query = {
            'name': {'$regex': '^{}'.format(cups[:20])},
            # KLUDGE: datetime is naive but is stored in mongo as UTC,
            # if we pass dates as local, we will be comparing to the equivalent
            # UTC date which is wrong, so we remove the timezone to make them naive
            'datetime': {'$gte': as_naive(start), '$lt': as_naive(end)}
        }

        match_query.update(extra_filter)

        query = [
            {'$match': match_query },
            {'$group': {
                '_id': {'datetime': '$datetime', 'name': '$name'},
                'datetime': {'$first': '$datetime'},
                'ai': {'$first': '$ai'},
                'season': {'$first': '$season'},
                }
            },
            {'$sort': {
                    'datetime': ASCENDING,
                }
            }
        ]

        return query

    def get_curve(self, curve_type, start, end, cups=None):
        query = self.build_query(start, end, cups, **curve_type.extra_filter)

        result = self.get_cursor_db(curve_type.model, query)

        for x in result:
            yield dict(
                season=x['season'],
                datetime=as_naive(x['datetime']),
                ai=float(x['ai']),
            )


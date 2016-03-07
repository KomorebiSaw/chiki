# coding: utf-8
from flask.ext import mongoengine
from . import fields, pagination


def _include_custom(obj):
    for key in fields.__all__:
        if not hasattr(obj, key):
            setattr(obj, key, getattr(fields, key))
    setattr(obj, 'abstract', abstract)


class MongoEngine(mongoengine.MongoEngine):

    def __init__(self, app=None):
        super(MongoEngine, self).__init__(app)
        _include_custom(self)

        self.Document = Document
        self.DynamicDocument = DynamicDocument


class BaseQuerySet(mongoengine.BaseQuerySet):

    def paginate(self, page, per_page, **kwargs):
        return pagination.Pagination(self, page, per_page, **kwargs)


class Document(mongoengine.Document):

    meta = {'abstract': True,
            'queryset_class': BaseQuerySet}


class DynamicDocument(mongoengine.DynamicDocument):

    meta = {'abstract': True,
            'queryset_class': BaseQuerySet}


def abstract(model):
    model._meta['abstract'] = True

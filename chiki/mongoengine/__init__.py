# coding: utf-8
from flask.ext import mongoengine
from . import fields, pagination


def _include_custom(obj):
    for key in fields.__all__:
        if not hasattr(obj, key):
            setattr(obj, key, getattr(fields, key))
    setattr(obj, 'abstract', abstract)


class Chocies(object):

    def __init__(self, **kwargs):
        self.CHOICES = []
        for key, value in kwargs.iteritems():
            self.CHOICES.append((key, value))
            setattr(self, key.upper(), value)
        self.DICT = dict(self.CHOICES)
        self.VALUES = self.DICT.keys()

    def text(self, key):
        return self.dict.get(key)


class MongoEngine(mongoengine.MongoEngine):

    def __init__(self, app=None):
        super(MongoEngine, self).__init__(app)
        _include_custom(self)

        self.Document = Document
        self.DynamicDocument = DynamicDocument

    def choices(self, **kwargs):
        return Chocies(**kwargs)


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

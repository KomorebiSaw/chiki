# coding: utf-8
from flask.ext.mongoengine import MongoEngine as _MongoEngine
from . import fields


def _include_custom(obj):
	for key in fields.__all__:
		if not hasattr(obj, key):
			setattr(obj, key, getattr(fields, key))


class MongoEngine(_MongoEngine):
	
	def __init__(self, app=None):
		super(MongoEngine, self).__init__(app)
		_include_custom(self)

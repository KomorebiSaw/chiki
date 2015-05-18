# coding: utf-8
from flask.ext.restful import Api

__all__ = [
	'api', 'success',
]

api = Api()


def success(**kwargs):
	return dict(code=0, key='SUCCESS', data=kwargs)
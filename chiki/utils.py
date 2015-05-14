# coding: utf-8
from flask import jsonify

__all__ = [
	'strip', 'json_success', 'json_error',
]


def strip(val, *args):
	if not val:
		return val

	if isinstance(val, dict):
		return dict((x, strip(y) if x not in args else y) for x, y in val.iteritems())
	if isinstance(val, list):
		return list(strip(x) for x in val)
	if hasattr(val, 'strip'):
		return val.strip()
	return val


def json_success(**kwargs):
	kwargs['code'] = 0
	return jsonify(kwargs)


def json_error(**kwargs):
	kwargs['code'] = -1
	return jsonify(kwargs)
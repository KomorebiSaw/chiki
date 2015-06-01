# coding: utf-8
import time
from flask import jsonify

__all__ = [
	'strip', 'json_success', 'json_error', 
	'datetime2best', 'time2best',
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


def datetime2best(input):
	return time2best(time.mktime(input.timetuple()))


def time2best(input):
	now = max(time.time(), input) + 8 * 3600
	tmp = input + 8 * 3600
	if tmp + 86400 < now // 86400 * 86400:
		if time.strftime('%Y', time.localtime(input)) == time.strftime('%Y', time.localtime()):
			return time.strftime('%m.%d', time.localtime(input))
		return time.strftime(u'%y年%m月', time.localtime(input))
	elif tmp < now // 86400 * 86400:
		return u'昨天'

	offset = now - tmp
	hours = offset // 3600
	if hours > 0:
		if hours >= 12: 
			hours = 12
		elif hours > 6:
			hours = hours // 2 * 2
		return u'%s小时前' % int(hours)

	minutes = offset // 60
	if minutes > 1:
		if minutes >= 30:
			minutes = 30
		elif minutes >= 10:
			minutes = minutes // 10 * 10
		elif minutes >= 5:
			minutes = 5
		return u'%s分钟前' % int(minutes)

	return u'刚刚'
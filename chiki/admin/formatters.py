# coding: utf-8
import time
from xml.sax.saxutils import escape, quoteattr
from ..jinja import markup


def format_span(text, short):
	if text.startswith('http://'):
		return markup('<a href=%s title=%s target="_blank">%s</a>' % (
			quoteattr(text), quoteattr(text), escape(short)))
	return markup('<span title=%s>%s</span>' % (quoteattr(text), escape(short)))


def format_len(max_len):
	def wrapper(view, context, model, name):
		if hasattr(model.__class__, name):
			data = unicode(getattr(model, name))
			if len(data) > max_len + 1:
				return format_span(data, data[:max_len] + '...')
			return data
		return ''
	return wrapper


def format_choices(view, context, model, name):
	if hasattr(model.__class__, name):
		field = getattr(model.__class__, name)
		data = getattr(model, name)
		choices = field.choices
		if choices:
			for key, value in choices:
				if key == data:
					return value
	return ''


def format_time(view, context, model, name):
	if hasattr(model, name):
		return str(getattr(model, name)).split('.')[0]
	return ''


def format_date(view, context, model, name):
	if hasattr(model, name):
		return str(getattr(model, name)).split(' ')[0]
	return ''


def format_best(view, context, model, name):
	if hasattr(model, name):
		attr = getattr(model, name)
		return format_span(str(attr).split('.')[0], datetime2best(attr))
	return ''


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
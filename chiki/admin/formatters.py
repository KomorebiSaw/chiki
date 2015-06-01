# coding: utf-8
from xml.sax.saxutils import escape as _escape, quoteattr
from ..jinja import markup, markupper
from ..utils import datetime2best, time2best


def quote(*args):
	return tuple(quoteattr(x) for x in args)


def escape(*args):
	return tuple(_escape(x) for x in args)


def get_span(text, short):
	if text.startswith('http://'):
		return '<a href=%s title=%s target="_blank">%s</a>' % (
			quote(text, text) + escape(short))
	return '<span title=%s>%s</span>' % (quote(text) + escape(short))


def formatter(func):
	def wrapper(view, context, model, name):
		if hasattr(model.__class__, name):
			data = unicode(getattr(model, name))
			return markup(func(data))
		return ''
	return wrapper


def formatter_model(func):
	def wrapper(view, context, model, name):
		return markup(func(model))
	return wrapper


def formatter_len(max_len):
	@formatter
	def wrapper(data):
		if len(data) > max_len + 1:
			return get_span(data, data[:max_len] + '...')
		return data
	return wrapper


def formatter_icon(func=None, height=40):
	@formatter_model
	def icon(model):
		tpl = u'''
			<a href=%%s target="_blank">
				<img src=%%s style="max-height: %dpx; margin: -6px">
			</a>
		''' % height
		url = func(model)
		return tpl % quote(url, url)
	return icon


@formatter
def format_time(t):
	return str(t).split('.')[0]


@formatter
def format_date(t):
	return str(t).split(' ')[0]


@formatter
def format_best(t):
	return get_span(str(t).split('.')[0], datetime2best(t))


def format_choices(view, context, model, name):
	if hasattr(model.__class__, name):
		field = getattr(model.__class__, name)
		data = getattr(model, name)
		choices = field.choices
		if choices:
			return dict(choices).get(data, data)

@markupper
def type_best(view, t):
	return get_span(str(t).split('.')[0], datetime2best(t))
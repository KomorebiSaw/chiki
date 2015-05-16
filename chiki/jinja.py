# coding: utf-8
from flask import current_app
from jinja2 import Markup

__all__ = [
	'markup', 'first_error', 'JinjaManager', 'init_jinja',
]


def markup(html):
	return Markup(html) if current_app.jinja_env.autoescape else html


def first_error(form):
	for field in form:
		if field.errors:
			return field.errors[0]


class JinjaManager(object):

	def __init__(self, app=None):
		if app is not None:
			self.init_app(app)

	def init_app(self, app):
		app.jinja_env.filters.update(self.filters)
		app.context_processor(self.context_processor)

	@property
	def filters(self):
		return dict(
			line2br=self.line2br_filter,
			kform=self.kform_filter,
			kfiled=self.kfield_filter,
			kform_inline=self.kform_inline_filter,
			kfield_inline=self.kfield_inline_filter,
			alert=self.alert_filter,
		)

	def context_processor(self):
		return dict(
			alert=self.alert_filter,
		)

	def line2br_filter(self, text):
		return markup(text.replace('\n', '<br>'))

	def kform_filter(self, form):
		out = []
		for field in form:
			out.append(self.kfield_filter(field))
		return markup(''.join(out))

	def kfield_filter(self, field, **kwargs):
		out = []
		if field.type in ['CSRFTokenField', 'HiddenField']:
			out.append(field(**kwargs))
		else:
			kwargs.setdefault('class_', 'form-control')
			kwargs.setdefault('data_label', field.label.text)
			out.append('<div class="form-group">')
			out.append(field.label(class_='control-label'))
			if hasattr(field, 'addon'):
				out.append('<div class="input-group">')
				out.append(field(**kwargs))
				out.append('<span class="input-group-addon">%s</span>' % field.addon)
				out.append('</div>')
			else:
				out.append(field(**kwargs))
			out.append('</div>')
		return markup(''.join(out)) 

	def kform_inline_filter(self, form):
		out = []
		for field in form:
			out.append(self.kfield_inline_filter(field))
		return markup(''.join(out))

	def kfield_inline_filter(self, field, **kwargs):
		out = []
		if field.type in ['CSRFTokenField', 'HiddenField']:
			out.append(field(**kwargs))
		else:
			out.append('<div class="form-group">')
			if field.type == 'BooleanField':
				out.append('<div class="checkbox"><label>%s %s</label></div>' 
					% (field(**kwargs), field.label.text))
			else:
				kwargs.setdefault('class_', 'form-control')
				kwargs.setdefault('data_label', field.label.text)
				kwargs.setdefault('placeholder', field.label.text)
				out.append(field(**kwargs))
			out.append('</div>')
		return markup(''.join(out))

	def alert_msg(self, msg, style='danger'):
		return markup('<div class="alert alert-%s"><button class="close" '
			'type="button" data-dismiss="alert" aria-hidden="true">&times;'
			'</button><span>%s</span></div>' % (style, msg))

	def alert_filter(self, form=None, style='danger'):
		error = first_error(form)
		if error:
			return self.alert_msg(error, style)
		return ''


def init_jinja(app):
	jinja = JinjaManager()
	jinja.init_app(app)
# coding: utf-8
from flask import url_for
from wtforms.widgets import html_params, HTMLString
from wtforms.compat import text_type
from cgi import escape

__all__ = [
	'VerifyCode', 'UEditor',
]


class VerifyCode(object):

	html_params = staticmethod(html_params)

	def __call__(self, field, **kwargs):
		if field.hidden == True:
			html = '<input %s>' % self.html_params(
				id=field.id,
				type='hidden',
				name=field.name,
				value=field._value(),
			)
		else:
			html = '<div class="input-group input-group-lg">'
			html += '<input %s>' % self.html_params(
				id=field.id,
				type='text',
				name=field.name,
				value=field._value(),
				maxlength=field.code_len,
				**kwargs
			)
			html += '<span class="input-group-addon" style=padding:0;"><img %s><span>' % self.html_params(
				id='%s_img' % field.id,
				src=url_for('verify_code', key=field.key),
				data_src=url_for('verify_code', key=field.key),
				style="cursor:pointer",
				onclick="$(this).attr('src', '" + url_for('verify_code', key=field.key) + "&t=' + Math.random());",
			)
			html += '</div>'
		return HTMLString(html)


class UEditor(object):

	html_params = staticmethod(html_params)

	def __call__(self, field, **kwargs):
		kwargs.setdefault('id', field.id)
		kwargs.setdefault('type', 'text/plain')
		kwargs.setdefault('style', 'width:99%;height:360px;')
		kwargs['class'] = ''
		return HTMLString(
			'<script %s>%s</script><script>var um = UM.getEditor("%s");</script>' % (
				self.html_params(name=field.name, **kwargs), 
				text_type(field._value()), 
				field.name,
			)
		)


class KListWidget(object):
	
	def __init__(self, html_tag='ul', sub_tag='li', sub_startswith='sub_', prefix_label=True):
		self.html_tag = html_tag
		self.sub_tag = sub_tag
		self.sub_startswith = sub_startswith
		self.prefix_label = prefix_label

	def __call__(self, field, **kwargs):
		kwargs.setdefault('id', field.id)
		sub_kwargs = dict((k[4:],v) for k, v in kwargs.iteritems() if k.startswith(self.sub_startswith))
		kwargs = dict(filter(lambda x: not x[0].startswith(self.sub_startswith), kwargs.iteritems()))
		sub_html = '%s %s' % (self.sub_tag, widgets.html_params(**sub_kwargs))
		html = ['<%s %s>' % (self.html_tag, widgets.html_params(**kwargs))]
		for subfield in field:
			if self.prefix_label:
				html.append('<%s>%s %s</%s>' % (sub_html, subfield.label, subfield(), self.sub_tag))
			else:
				html.append('<%s>%s %s</%s>' % (sub_html, subfield(), subfield.label, self.sub_tag))
		html.append('</%s>' % self.html_tag)
		return widgets.HTMLString(''.join(html))
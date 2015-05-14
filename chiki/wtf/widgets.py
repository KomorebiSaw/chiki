# coding: utf-8
from wtforms.widgets import HTMLString, html_params


class FileInput(object):

	template = """
		<div>
			<i class="icon-file"></i>%(name)s %(size)dk
		</div>
	"""

	def __call__(self, field, **kwargs):
		kwargs.setdefault('id', field.id)

		placeholder = ''
		if field.data and field.data.filename:
			placeholder = self.template % dict(name=field.data.filename, size=0)

		return HTMLString('%s<input %s>' % (placeholder, 
			html_params(name=field.name, type='file', **kwargs)))


class ImageInput(object):

	template = """
		<div class="image-thumbnail">
			<img src="%(thumb)s">
		</div>
	"""

	def __call__(self, field, **kwargs):
		kwargs.setdefault('id', field.id)

		placeholder = ''
		if field.data and hasattr(field.data, 'url') and field.data.url:
			placeholder = self.template % dict(thumb=field.data.url)

		return HTMLString('%s<input %s>' % (placeholder, 
			html_params(name=field.name, type='file', **kwargs)))


class AreaInput(object):

	template = ('<select %s></select><select %s></select>'
			'<select %s></select><script type="text/javascript">'
			'area.init("%s", "%s", "%s", "%s")</script>')

	def __call__(self, field, **kwargs):
		datas = (field.data or '').split('|')
		if len(datas) == 3:
			province, city, county = datas
		else:
			province, city, county = '', '', ''
		province_name = '%s_province' % field.name
		city_name = '%s_city' % field.name
		county_name = '%s_county' % field.name
		return HTMLString(self.template % (
			html_params(id=province_name, name=province_name, **kwargs),
			html_params(id=city_name, name=city_name, **kwargs),
			html_params(id=county_name, name=county_name, **kwargs),
			field.name, province, city, county,
		))

# coding: utf-8
from flask.ext.admin.contrib.mongoengine.form import CustomModelConverter
from flask.ext.mongoengine.wtf import orm
from ..forms.fields import FileField, ImageField, AreaField


class KModelConverter(CustomModelConverter):

	@orm.converts('XFileField')
	def conv_kfile(self, model, field, kwargs):
		return FileField(size=field.size, allows=field.allows, **kwargs)

	@orm.converts('XImageField')
	def conv_kimage(self, model, field, kwargs):
		return ImageField(size=field.size, allows=field.allows, **kwargs)

	@orm.converts('AreaField')
	def conv_area(self, model, field, kwargs):
		return AreaField(**kwargs)
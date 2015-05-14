# coding: utf-8
from flask.ext.admin.model.filters import convert as _convert
from flask.ext.admin.contrib.mongoengine.filters import (
	BaseMongoEngineFilter, FilterEqual, FilterNotEqual, FilterConverter
)


class BaseReferenceFilter(BaseMongoEngineFilter):

	def __init__(self, column, name, ref_type=None, options=None, data_type=None):
		super(BaseReferenceFilter, self).__init__(column, name, options, data_type)
		self.ref_type = ref_type
	
	def clean(self, value):
		if self.ref_type == int:
			return int(float(value))
		elif self.ref_type == float:
			return float(value)
		return value


class ReferenceEqualFilter(FilterEqual, BaseReferenceFilter):
	pass


class ReferenceNotEqualFilter(FilterNotEqual, BaseReferenceFilter):
	pass


class KFilterConverter(FilterConverter):

	reference_filters = (ReferenceEqualFilter, ReferenceNotEqualFilter)

	def convert(self, type_name, column, name, ref_type=None):
		filter_name = type_name.lower()

		if filter_name in self.converters:
			if ref_type:
				return self.converters[filter_name](column, name, ref_type)
			else:
				return self.converters[filter_name](column, name)

		return None

	@_convert('ReferenceField')
	def conv_reference(self, column, name, ref_type=None):
		return [f(column, name, ref_type) for f in self.reference_filters]
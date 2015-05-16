# coding: utf-8
from mongoengine.fields import IntField, LongField, DecimalField
from mongoengine.fields import FloatField, ReferenceField
from flask.ext.admin.contrib.mongoengine import ModelView as _ModelView
from flask.ext.admin.contrib.sqla import ModelView as _SModelView
from flask.ext.admin._compat import string_types
from .convert import KModelConverter
from .filters import KFilterConverter

__all__ = [
	"ModelView", "SModelView",
]


class ModelView(_ModelView):

	page_size = 50
	model_form_converter = KModelConverter
	filter_converter = KFilterConverter()

	def __init__(self, model, name=None,
			category=None, endpoint=None, url=None, static_folder=None,
			menu_class_name=None, menu_icon_type=None, menu_icon_value=None):
		if not self.column_labels:
			self.column_labels = {}
		for field in model._fields:
			if field not in self.column_labels:
				verbose_name = getattr(model, field).verbose_name
				if verbose_name:
					self.column_labels[field] = verbose_name
		super(ModelView, self).__init__(model, name, category, endpoint, url, static_folder,
										menu_class_name=menu_class_name,
										menu_icon_type=menu_icon_type,
										menu_icon_value=menu_icon_value)

	def create_model(self, form):
		try:
			model = self.model()
			self.pre_model_change(form, model, True)
			form.populate_obj(model)
			self._on_model_change(form, model, True)
			model.save()
		except Exception as ex:
			if not self.handle_view_exception(ex):
				flash('Failed to create record. %(error)s' % dict(error=format_error(ex)), 'error')
			return False
		else:
			self.after_model_change(form, model, True)

		return True

	def update_model(self, form, model):
		try:
			self.pre_model_change(form, model, False)
			form.populate_obj(model)
			self._on_model_change(form, model, False)
			model.save()
		except Exception as ex:
			if not self.handle_view_exception(ex):
				flash('Failed to update record. %(error)s' % dict(error=format_error(ex)), 'error')
			return False
		else:
			self.after_model_change(form, model, False)

		return True

	def pre_model_change(self, form, model, created=False):
		pass

	def scaffold_filters(self, name):
		if isinstance(name, string_types):
			attr = self.model._fields.get(name)
		else:
			attr = name

		if attr is None:
			raise Exception('Failed to find field for filter: %s' % name)

		# Find name
		visible_name = None

		if not isinstance(name, string_types):
			visible_name = self.get_column_name(attr.name)

		if not visible_name:
			visible_name = self.get_column_name(name)

		# Convert filter
		type_name = type(attr).__name__
		if isinstance(attr, ReferenceField):
			document, ref_type = attr.document_type, None
			if hasattr(document, 'id'):
				xattr = document._fields.get('id')
				if isinstance(xattr, IntField) or isinstance(xattr, LongField):
					ref_type = int
				elif isinstance(xattr, DecimalField) or isinstance(xattr, FloatField):
					ref_type = float
			flt = self.filter_converter.convert(type_name, attr, visible_name, ref_type)
		else:
			flt = self.filter_converter.convert(type_name, attr, visible_name)

		return flt


class SModelView(_SModelView):

	def __init__(self, model, session,
			name=None, category=None, endpoint=None, url=None, static_folder=None,
			menu_class_name=None, menu_icon_type=None, menu_icon_value=None):
		if hasattr(model, 'labels'):
			self.column_labels = model.labels
		super(SModelView, self).__init__(model, session, name=name, category=category, 
			endpoint=endpoint, url=url, static_folder=static_folder, menu_class_name=menu_class_name,
			menu_icon_type=menu_icon_type, menu_icon_value=menu_icon_value)
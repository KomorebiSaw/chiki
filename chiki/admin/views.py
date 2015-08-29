# coding: utf-8
from datetime import datetime
from flask import current_app, redirect, flash
from flask.ext.admin import AdminIndexView, expose
from flask.ext.admin.actions import action
from flask.ext.admin.babel import gettext, ngettext, lazy_gettext
from flask.ext.admin.contrib.mongoengine import ModelView as _ModelView
from flask.ext.admin.contrib.mongoengine.helpers import format_error
from flask.ext.admin.contrib.sqla import ModelView as _SModelView
from flask.ext.admin._compat import string_types
from mongoengine.fields import IntField, LongField, DecimalField, FloatField
from mongoengine.fields import StringField, ReferenceField, ObjectIdField, ListField
from bson.objectid import ObjectId
from .convert import KModelConverter
from .filters import KFilterConverter
from .formatters import type_best, type_image, type_file
from ..mongoengine.fields import FileProxy, ImageProxy

__all__ = [
    "ModelView", "SModelView", "IndexView",
]


class ModelView(_ModelView):

    list_template = 'xadmin/model/list.html'

    page_size = 50
    model_form_converter = KModelConverter
    filter_converter = KFilterConverter()

    column_type_formatters = _ModelView.column_type_formatters or dict()
    column_type_formatters[datetime] = type_best
    column_type_formatters[FileProxy] = type_file

    show_popover = False

    def __init__(self, model, name=None,
            category=None, endpoint=None, url=None, static_folder=None,
            menu_class_name=None, menu_icon_type=None, menu_icon_value=None):

        # 初始化标识
        self.column_labels = self.column_labels or dict()
        for field in model._fields:
            if field not in self.column_labels:
                verbose_name = getattr(model, field).verbose_name
                if verbose_name:
                    self.column_labels[field] = verbose_name

        # 初始化选择列
        self.column_choices = self.column_choices or dict()
        for field in model._fields:
            if field not in self.column_choices:
                choices = getattr(model, field).choices
                if choices:
                    self.column_choices[field] = choices


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
            current_app.logger.error(ex)
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
            current_app.logger.error(ex)
            if not self.handle_view_exception(ex):
                flash('Failed to update record. %(error)s' % dict(error=format_error(ex)), 'error')
            return False
        else:
            self.after_model_change(form, model, False)

        return True

    def pre_model_change(self, form, model, created=False):
        pass

    def get_ref_type(self, attr):
        document, ref_type = attr.document_type, None
        if hasattr(document, 'id'):
            xattr = document._fields.get('id')
            if isinstance(xattr, IntField) or isinstance(xattr, LongField):
                ref_type = int
            elif isinstance(xattr, DecimalField) or isinstance(xattr, FloatField):
                ref_type = float
            elif isinstance(xattr, ObjectIdField):
                ref_type = ObjectId
        return ref_type

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
            ref_type = self.get_ref_type(attr)
            flt = self.filter_converter.convert(type_name, attr, visible_name, ref_type)
        elif isinstance(attr, ListField) and isinstance(attr.field, ReferenceField):
            ref_type = self.get_ref_type(attr.field)
            flt = self.filter_converter.convert(type_name, attr, visible_name, ref_type)
        elif isinstance(attr, ObjectIdField):
            flt = self.filter_converter.convert(type_name, attr, visible_name, ObjectId)
        else:
            flt = self.filter_converter.convert(type_name, attr, visible_name)

        return flt

    def get_list(self, page, sort_column, sort_desc, search, filters,
                 execute=True):
        query = self.get_query()
        if self._filters:
            for flt, flt_name, value in filters:
                f = self._filters[flt]
                query = f.apply(query, f.clean(value))

        if self._search_supported and search:
            query = self._search(query, search)

        count = query.count() if not self.simple_list_pager else None

        if sort_column:
            query = query.order_by('%s%s' % ('-' if sort_desc else '', sort_column))
        else:
            order = self._get_default_order()
            if order:
                if order[1] != True and order[1] != False:
                    query = query.order_by(*order)
                else:
                    query = query.order_by('%s%s' % ('-' if order[1] else '', order[0]))

        # Pagination
        if page is not None:
            query = query.skip(page * self.page_size)

        query = query.limit(self.page_size)

        if execute:
            query = query.all()

        return count, query

    @action('delete',
            lazy_gettext('Delete'),
            lazy_gettext('Are you sure you want to delete selected records?'))
    def action_delete(self, ids):
        try:
            count = 0

            id = self.model._meta['id_field']
            if id in self.model._fields:
                if isinstance(self.model._fields[id], IntField):
                    all_ids = [int(pk) for pk in ids]
                elif isinstance(self.model._fields[id], StringField):
                    all_ids = ids
                else:
                    all_ids = [self.object_id_converter(pk) for pk in ids]
            else:
                all_ids = [self.object_id_converter(pk) for pk in ids]

            for obj in self.get_query().in_bulk(all_ids).values():
                count += self.delete_model(obj)

            flash(ngettext('Record was successfully deleted.',
                           '%(count)s records were successfully deleted.',
                           count,
                           count=count))
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to delete records. %(error)s', error=str(ex)),
                      'error')


class SModelView(_SModelView):

    def __init__(self, model, session,
            name=None, category=None, endpoint=None, url=None, static_folder=None,
            menu_class_name=None, menu_icon_type=None, menu_icon_value=None):
        if hasattr(model, 'LABELS'):
            self.column_labels = model.LABELS
        super(SModelView, self).__init__(model, session, name=name, category=category, 
            endpoint=endpoint, url=url, static_folder=static_folder, menu_class_name=menu_class_name,
            menu_icon_type=menu_icon_type, menu_icon_value=menu_icon_value)


class IndexView(AdminIndexView):

    @expose('/')
    def index(self):
        return redirect(current_app.config.get('INDEX_REDIRECT'))
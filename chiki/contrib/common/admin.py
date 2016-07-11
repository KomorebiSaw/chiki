# coding: utf-8
import json
from chiki.admin import ModelView, formatter_len, formatter_icon
from chiki.admin import formatter_text, formatter_link
from chiki.forms.fields import WangEditorField, KCheckboxField, DragSelectField
from chiki.utils import json_success
from datetime import datetime
from wtforms.fields import TextAreaField, SelectField
from flask import current_app, url_for, request
from flask.ext.admin import expose
from flask.ext.admin.form import BaseForm
from .models import View, Item

FA = '<i class="fa fa-%s"></i>'


class ItemView(ModelView):
    column_default_sort = ('key', False)
    column_list = ('name', 'key', 'type', 'value', 'modified', 'created')
    column_center_list = ('type', 'modified', 'created')
    column_filters = ('key', 'modified', 'created')
    column_formatters = dict(value=formatter_len(32))

    form_overrides = dict(value=TextAreaField)

    def pre_model_change(self, form, model, create=False):
        if model.type == model.TYPE_INT:
            try:
                self.value = int(form.value.data)
            except:
                self.value = int(model.value or 0)

    def on_model_change(self, form, model, create=False):
        if model.type == model.TYPE_INT:
            model.value = self.value


class StatLogView(ModelView):
    column_default_sort = ('created', True)
    column_list = ('key', 'tid', 'day', 'hour', 'value', 'modified', 'created')
    column_center_list = ('day', 'hour', 'modified', 'created')
    column_filters = ('key', 'tid', 'day', 'hour', 'value', 'modified', 'created')
    column_searchable_list = ('key', 'tid', 'day')


class TraceLogView(ModelView):
    column_default_sort = ('created', True)
    column_filters = ('key', 'tid', 'user', 'label', 'created')
    column_searchable_list = ('key', 'tid', 'label')
    column_formatters = dict(
        value=formatter_len(40),
    )


class ChannelView(ModelView):
    column_default_sort = ('created', )
    column_center_list = ('id', 'name', 'modified', 'created')
    column_formatters = dict(
        desc=formatter_len(),
    )
    column_searchable_list = ('name',)
    column_filters = ('id', 'created')
    form_excluded_columns = ('id',)

    def on_model_change(self, form, model, created=False):
        model.create()
        model.modified = datetime.now()


class AndroidVersionView(ModelView):
    column_default_sort = ('created', True)
    column_formatters = dict(
        log=formatter_len(),
        url=formatter_len(),
    )
    column_searchable_list = ('version',)
    column_filters = ('id', 'version', 'enable', 'created')
    column_center_list = ('enable', 'id', 'version', 'modified', 'created')
    form_excluded_columns = ('id',)

    def on_model_change(self, form, model, created=False):
        model.create()
        model.modified = datetime.now()


class IOSVersionView(ModelView):
    column_default_sort = ('created', True)
    column_formatters = dict(
        log=formatter_len(),
        url=formatter_len(),
    )
    column_searchable_list = ('version',)
    column_filters = ('id', 'version', 'enable', 'created')
    column_center_list = ('enable', 'id', 'version', 'modified', 'created',)
    form_excluded_columns = ('id',)

    def on_model_change(self, form, model, created=False):
        model.create()
        model.modified = datetime.now()


class APIItemView(ModelView):
    column_default_sort = ('created', True)
    column_searchable_list = ('key', 'name')
    column_filters = ('key', 'modified', 'created')
    column_center_list = ('modified', 'created')

    def on_model_change(self, form, model, created=False):
        model.modified = datetime.now()


class UserImageView(ModelView):

    column_default_sort = ('created', True)
    column_filters = ('source', 'modified', 'created')
    column_center_list = ('modified', 'created')

    def on_model_change(self, form, model, created=False):
        model.modified = datetime.now()


class ActionItemView(ModelView):

    column_default_sort = ('created', True)
    column_filters = (
        'name', 'key', 'module', 'action', 'url', 'login',
        'sort', 'enable', 'modified', 'created'
    )
    column_center_list = ('icon', 'module', 'sort', 'enable', 'modified', 'created')
    column_formatters = dict(
        icon=formatter_icon(lambda m: (m.icon.get_link(height=40), m.icon.link)),
        name=formatter_text(lambda m: (m.name, m.name), max_len=7),
    )


class SlideItemView(ModelView):
    column_labels = dict(modified='修改', created='创建')
    column_default_sort = ('module', 'sort')
    column_default_sort = ('modified', True)
    column_searchable_list = ('name', )
    column_filters = ('module', 'modified', 'created')
    column_center_list = (
        'module', 'share', 'sort', 'enable', 'modified', 'created',
    )
    column_formatters = dict(
        image=formatter_icon(lambda m: (m.image.get_link(height=40), m.image.link)),
        url=formatter_len(30)
    )

    def on_model_change(self, form, model, created=False):
        model.modified = datetime.now()


class ImageItemView(ModelView):
    pass


class TPLItemView(ModelView):
    pass


class ActionModuleView(ModelView):
    pass


class SlideModuleView(ModelView):
    pass


class OptionItemView(ModelView):
    pass


def get_link(key):
    url = url_for('page2', key=key)
    if current_app.config.get('WEB_HOST'):
        return 'http://%s%s' % (current_app.config.get('WEB_HOST'), url)
    return url


class PageView(ModelView):
    column_default_sort = ('-created', )
    column_list = ('id', 'key', 'name', 'content', 'modified', 'created')
    column_center_list = ('id', 'key', 'modified', 'created')
    column_formatters = dict(
        id=formatter_link(lambda m: (m.id, get_link(str(m.id)))),
        key=formatter_link(lambda m: (m.key, get_link(str(m.key)))),
    )
    form_excluded_columns = ('id', )
    form_overrides = dict(content=WangEditorField)

    def on_model_change(self, form, model, created=False):
        model.create()
        model.modified = datetime.now()


class ChoicesView(ModelView):
    pass


class MenuView(ModelView):
    pass


class ModelAdminView(ModelView):
    pass


class Form(BaseForm):

    def __init__(self, formdata=None, obj=None, prefix=u'', **kwargs):
        self._obj = obj
        super(BaseForm, self).__init__(formdata=formdata, obj=obj, prefix=prefix, **kwargs)
        if self._obj and self._obj.model:
            choices = []
            model = current_app.cool_manager.models.get(self._obj.model.name)
            if current_app.cool_manager and not current_app.cool_manager.loading:
                for admin in current_app.extensions.get('admin', []):
                    for view in admin._views:
                        if hasattr(view, 'model') and view.model is self._obj.__class__:
                            for x in model._fields:
                                attr = getattr(model, x)
                                choices.append((x, view.column_labels.get(x) or attr.verbose_name))
                            break
            if current_app.cool_manager and not current_app.cool_manager.loading:
                for admin in current_app.extensions.get('admin', []):
                    for view in admin._views:
                        if hasattr(view, 'model') and view.model is model:
                            for x in view.column_formatters.iterkeys():
                                if x not in model._fields:
                                    choices.append((x, view.column_labels.get(x, x)))
                            break
            for field in self:
                if type(field) == DragSelectField:
                    field.choices = choices

            if hasattr(model, '_meta'):
                indexes = model._meta.get('indexes', [])
                attr = getattr(self, 'column_default_sort')
                choices = [(json.dumps(x), json.dumps(x)) for x in indexes]
                if not choices and hasattr(model, 'created'):
                    choices.append(('"-created"', '"-created"'))
                choices.append(('""', '空'))
                attr.choices = choices


class ViewView(ModelView):
    tabs = [
        dict(endpoint='.set_menu', title='菜单', text='菜单'),
    ]
    form_overrides = dict(
        column_default_sort=SelectField,
        column_list=DragSelectField,
        column_center_list=DragSelectField,
        column_hidden_list=DragSelectField,
        column_filters=DragSelectField,
        column_sortable_list=DragSelectField,
        column_searchable_list=DragSelectField,
        form_excluded_columns=DragSelectField,
    )
    form_args = dict(column_default_sort=dict(choices=[]))
    form_base_class = Form

    column_list = ["name", "label", "type", "page_size", "can_create", "can_edit", "can_delete", "icon", "modified", "created", "code"]
    column_center_list = ["type", "page_size", "can_delete", "can_edit", "can_create", "icon", "code", "modified", "created"]
    column_hidden_list = ["modified"]
    column_filters = ["id", "model", "type", "can_create", "can_edit", "can_delete", "modified", "created"]
    column_searchable_list = ["name", "label"]
    form_excluded_columns = ["model"]
    column_formatters = dict(
        icon=formatter_link(lambda m: (FA % (m.icon or 'file-o'), '/admin/view/get_icon?id=%s' % m.id),
            html=True,
            id=lambda m: str(m.id) + '-icon',
            class_='btn btn-default btn-sm btn-icon',
            data_id=lambda m: m.id,
            data_key='icon',
            data_toggle="modal",
            data_target="#simple-modal",
            data_refresh="true",
        ),
        code=formatter_link(lambda m: (FA % 'code',
                '/admin/view/get_code?id=%s' % m.id) if m.code_text else ('', ''),
            html=True,
            id=lambda m: str(m.id) + '-icon',
            class_='btn btn-default btn-sm btn-code',
            data_id=lambda m: m.id,
            data_key='code',
            data_toggle="modal",
            data_target="#simple-modal",
            data_refresh="true",
        ),
    )

    @expose('/get_icon')
    def get_icon(self):
        obj = self.model.objects(id=request.args.get('id')).get_or_404()
        return self.render('common/icon-modal.html', obj=obj)

    @expose('/get_code')
    def get_code(self):
        obj = self.model.objects(id=request.args.get('id')).get_or_404()
        return self.render('common/code-modal.html', obj=obj)

    @expose('/set_menu')
    def set_menu(self):
        menus = json.loads(Item.data('admin_menus', '[]', name='管理菜单'))
        views = dict()
        cates = dict()
        for view in View.objects.all():
            if view.type == view.TYPE_CATE:
                cates[view.name] = dict(id=view.name, name=view.label, icon=view.icon, children=[])
            else:
                views[view.name] = dict(id=view.name, name=view.label, icon=view.icon)
        if menus:
            right = []
            for menu in menus:
                if menu['id'] in views:
                    item = views[menu['id']]
                    right.append(item)
                    del views[menu['id']]
                elif menu['id'] in cates:
                    item = cates[menu['id']]
                    if 'children' in item and 'children' in menu:
                        for child in menu['children']:
                            if child['id'] in views:
                                item['children'].append(views[child['id']])
                                del views[child['id']]
                    right.append(item)
                    del cates[menu['id']]
        else:
            right = [dict(name='仪表盘', icon='diamond')]
        return self.render('common/menu.html', cates=cates, views=views, right=right)

    @expose('/save_menu', methods=['POST'])
    def save_menu(self):
        menus = request.form.get('menus')
        Item.set_data('admin_menus', menus, name='管理菜单')
        for admin in current_app.extensions.get('admin', []):
            admin._refresh()
        return json_success(msg='保存成功')

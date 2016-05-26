# coding: utf-8
from chiki.admin import ModelView, formatter_len, formatter_icon
from chiki.admin import formatter_text, formatter_link
from chiki.forms.fields import WangEditorField
from datetime import datetime
from wtforms.fields import TextAreaField
from flask import current_app, url_for


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
        name=formatter_text(lambda m: (m.name,m.name), max_len=7),
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

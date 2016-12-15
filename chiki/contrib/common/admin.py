# coding: utf-8
import json
import urllib
import qrcode as _qrcode
from PIL import Image
from StringIO import StringIO
from chiki.admin import ModelView, formatter_len, formatter_icon, formatter, formatter_model
from chiki.admin import formatter_text, formatter_link, popover, quote, escape
from chiki.forms.fields import WangEditorField, DragSelectField
from chiki.stat import statistics
from chiki.utils import json_success
from datetime import datetime
from wtforms.fields import TextAreaField, SelectField
from flask import current_app, url_for, request
from flask.ext.admin import expose
from flask.ext.admin.form import BaseForm
from .models import View, Item

FA = '<i class="fa fa-%s"></i>'


class ItemView(ModelView):
    column_default_sort = ('key', True)
    column_list = ('key', 'name',  'value', 'type', 'modified', 'created')
    column_center_list = ('type', 'modified', 'created')
    column_filters = ('key', 'modified', 'created')
    column_formatters = dict(value=formatter_len(32))
    column_searchable_list = ('key', 'name')
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
    column_center_list = ('day', 'hour', 'modified', 'created', 'value')
    column_filters = ('key', 'tid', 'day', 'hour', 'value', 'modified', 'created')
    column_searchable_list = ('key', 'tid', 'day')


class TraceLogView(ModelView):
    column_default_sort = ('created', True)
    column_filters = ('key', 'tid', 'user', 'label', 'created')
    column_searchable_list = ('key', 'tid', 'label')
    column_center_list = ('user', 'created')
    column_formatters = dict(
        value=formatter_len(40),
    )


class ShareLogView(ModelView):
    column_default_sort = ('created', True)
    column_list = ('user', 'image', 'title', 'link', 'status', 'media', 'created')
    column_center_list = ('created', 'user', 'status', 'media', 'image')
    column_searchable_list = ('title', 'desc', 'link', 'image')
    column_filters = ('user', 'title', 'desc', 'link', 'image', 'created')
    column_formatters = dict(
        image=formatter_icon(lambda m: m.image),
        title=formatter_text(lambda m: (m.title, m.desc, 'text-success' if m.desc else '')),
        )


class ImageItemView(ModelView):
    column_center_list = ('image', 'created')
    column_filters = ('created',)


def create_qrcode(url):
    A, B, C = 480, 124, 108
    qr = _qrcode.QRCode(
        version=2, box_size=10, border=1,
        error_correction=_qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    im = qr.make_image()
    im = im.convert("RGBA")
    im = im.resize((A, A), Image.BILINEAR)

    em = Image.new("RGBA", (B, B), "white")
    im.paste(em, ((A - B) / 2, (A - B) / 2), em)

    with open(current_app.get_data_path('logo.jpg')) as fd:
        icon = Image.open(StringIO(fd.read()))
    icon = icon.resize((C, C), Image.ANTIALIAS)
    icon = icon.convert("RGBA")
    im.paste(icon, ((A - C) / 2, (A - C) / 2), icon)

    stream = StringIO()
    im.save(stream, format='png')
    return dict(stream=stream, format='png')


@statistics(modal=True)
class ChannelView(ModelView):
    column_labels = dict(stat='统计')
    column_list = ['id', 'name', 'password', 'url', 'image', 'modified', 'created', 'stat']
    column_center_list = ['id', 'image', 'modified', 'created', 'stat']
    form_excluded_columns = ('id',)
    column_searchable_list = ('name', 'url')

    column_formatters = dict(
        stat=formatter_link(lambda m: (
            '<i class="fa fa-line-chart"></i>',
            '/admin/channel/stat?%s' % urllib.urlencode(dict(id=str(m.id)))),
            html=True, class_='btn btn-default btn-sm',
            data_toggle="modal",
            data_target="#simple-modal",
            data_refresh="true",
        ),
        url=formatter_link(lambda m: (
            'http://%s/outer/login/%d' % (current_app.config.get('WEB_HOST'), m.id),
            'http://%s/outer/login/%d' % (current_app.config.get('WEB_HOST'), m.id))
        ),
    )

    datas = dict(
        stat=[
            dict(title='注册用户', suffix='人', series=[
                dict(name='汇总', key='channel_user_new'),
            ]),
            dict(title='活跃用户', suffix='人', series=[
                dict(name='汇总', key='channel_user_active'),
            ]),
        ],
    )

    def on_model_change(self, form, model, created=False):
        model.create()
        model.modified = datetime.now()

        if hasattr(current_app, 'wxclient'):
            if not model.url:
                data = dict(
                    action_name='QR_LIMIT_SCENE',
                    action_info=dict(scene=dict(scene_id=model.id)),
                )
                model.url = current_app.wxclient.create_qrcode(**data).get('url')
                model.image = create_qrcode(model.url)
            elif not model.image:
                model.image = create_qrcode(model.url)


class QRCodeView(ModelView):
    column_list = ['user', 'image', 'url', 'modified', 'created']
    column_center_list = ['user', 'image', 'modified', 'created']
    column_filters = ['user', 'url', 'modified', 'created']
    column_searchable_list = ('url',)

    def on_model_change(self, form, model, created=False):
        if model.user:
            model.get(model.user)


class AndroidVersionView(ModelView):
    column_default_sort = ('created', True)
    column_formatters = dict(
        log=formatter_len(),
        url=formatter_len(),
    )
    column_searchable_list = ('version',)
    column_filters = ('id', 'version', 'enable', 'created')
    column_center_list = ('enable', 'id', 'version', 'modified', 'created')
    column_searchable_list = ('version',)
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


class APIView(ModelView):
    page_size = 200
    column_default_sort = ('created', True)
    column_searchable_list = ('key', 'name')
    column_filters = ('key', 'url', 'modified', 'created')
    column_center_list = ('modified', 'created', 'expire', 'cache')

    def on_model_change(self, form, model, created=False):
        model.modified = datetime.now()


class UserImageView(ModelView):

    column_default_sort = ('created', True)
    column_filters = ('source', 'modified', 'created')
    column_center_list = ('modified', 'created')

    def on_model_change(self, form, model, created=False):
        model.modified = datetime.now()


@formatter
def formatter_share(share):
    if share.title and share.url:
        return popover(
            '<img src=%s style="width:100px; height: auto;"></br><a href=%s>%s</a>' % (
                quote(share.image.get_link(), share.url) + escape(share.url)),
            '查看',
            share.title,
        )


@formatter_model
def formatter_A(model):
    icon = '<div class="A"><img src=%s style="height: 40px; width: auto;"></div>' % model.icon.link if model.icon else ''
    active = '<div class="B"><img src=%s style="height: 40px; width: auto;"></div>' % model.active_icon.link if model.active_icon else ''
    html = '<div class="C">%s%s</div>' % (icon, active)
    return html


@formatter_model
def format_android(model):
    if model.android_start and model.android_end:
        return '%s ~ %s' % (model.android_start.version, model.android_end.version)

    if model.android_start:
        return '%s' % model.android_start.version

    if model.android_end:
        return '%s' % model.android_end.version
    return ''


@formatter_model
def format_ios(model):
    if model.ios_start and model.ios_end:
        return '%s ~ %s' % (model.ios_start.version, model.android_end.version)

    if model.ios_start:
        return '%s' % model.ios_start.version

    if model.ios_end:
        return '%s' % model.ios_end.version
    return ''


class ActionView(ModelView):
    page_size = 200
    show_popover = True
    column_default_sort = ('module', 'sort')
    column_labels = dict(modified='修改', created='创建', android='安卓版本', ios='IOS版本')
    column_searchable_list = ('key', 'name')
    column_filters = (
        'id', 'name', 'module', 'login', 'sort', 'enable', 'modified', 'created'
    )
    column_list = (
        'icon', 'key', 'name', 'target', 'share', 'module', 'android', 'ios', 'login',
        'login_show', 'debug', 'sort', 'enable', 'modified', 'created'
    )
    column_center_list = (
        'icon', 'module', 'sort', 'enable', 'login', 'share', 'modified',
        'created', 'login_show', 'debug', 'android', 'ios'
    )
    column_hidden_list = ('debug', 'android', 'ios', 'login_show', 'target')
    column_formatters = dict(
        # icon=formatter_icon(lambda m: (m.icon.get_link(height=40), m.icon.link)),
        name=formatter_text(lambda m: (m.name, m.data, 'text-success' if m.data else ''), max_len=7),
        icon=formatter_A,
        share=formatter_share,
        android=format_android,
        ios=format_ios,
        )
    html = """
   <style type="text/css">
        .col-icon{
            background-color: #B2DFEE;
        }
        .column-header{background-color: #FFFFFF;}
        .C {position: relative; }
        .B {
            display: none;
            position: absolute;
            top: -9px;
            right: -68px;
            padding: 9px;
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
        }
        .A:hover + .B {
            display: block;
        }
    </style>
    """


class SlideView(ModelView):
    page_size = 200
    show_popover = True
    column_labels = dict(modified='修改', created='创建', android='安卓版本', ios='IOS版本')
    column_default_sort = ('module', 'sort')
    column_searchable_list = ('name', 'key')
    column_filters = ('module', 'modified', 'created')
    column_list = (
        'icon', 'key', 'name', 'target', 'share', 'module', 'android', 'ios', 'login',
        'login_show', 'debug', 'sort', 'enable', 'modified', 'created'
    )
    column_center_list = (
        'icon', 'key', 'name', 'module', 'sort', 'share',
        'android', 'ios', 'login', 'login_show', 'debug',
        'enable', 'modified', 'created'
    )
    column_hidden_list = ('debug', 'android', 'ios', 'login_show', 'target')
    column_formatters = dict(
        image=formatter_icon(lambda m: (m.image.get_link(height=40), m.image.link)),
        share=formatter_share,
        android=format_android,
        ios=format_ios,
    )

    def on_model_change(self, form, model, created=False):
        model.modified = datetime.now()


class ImageView(ModelView):
    pass


class TPLView(ModelView):
    page_size = 200
    column_center_list = ('name', 'key', 'enable', 'modified', 'created')
    column_searchable_list = ('name', 'key')
    column_filters = ('key', 'name')


class OptionView(ModelView):
    page_size = 200
    column_searchable_list = ('name', 'key')
    column_filters = ('key', 'name')


def get_link(key):
    url = url_for('page2', key=key)
    if current_app.config.get('WEB_HOST'):
        return 'http://%s%s' % (current_app.config.get('WEB_HOST'), url)
    return url


class PageView(ModelView):
    column_default_sort = ('-created', )
    column_list = ('id', 'key', 'name', 'content', 'modified', 'created')
    column_center_list = ('id', 'modified', 'created')
    column_searchable_list = ('name', 'key')
    column_filters = ('key', 'name')
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
    column_searchable_list = ('name', 'key')
    column_filters = ('key', 'name')
    column_center_list = ('modified', 'created', 'enable', 'default')
    column_hidden_list = ('default',)


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
    column_hidden_list = ["code",  "can_create", "can_edit", "can_delete"]
    column_searchable_list = ["name", "label"]
    form_excluded_columns = ["model"]
    column_formatters = dict(
        icon=formatter_link(lambda m: (
            FA % (m.icon or 'file-o'), '/admin/view/get_icon?id=%s' % m.id),
            html=True,
            id=lambda m: str(m.id) + '-icon',
            class_='btn btn-default btn-sm btn-icon',
            data_id=lambda m: m.id,
            data_key='icon',
            data_toggle="modal",
            data_target="#simple-modal",
            data_refresh="true",
        ),
        code=formatter_link(lambda m: (
            FA % 'code',
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

# coding: utf-8
import json
import time
from chiki.base import db
from chiki.utils import today
from datetime import datetime
from flask import current_app
from flask.ext.login import current_user


class Enable(object):
    """ 状态选项 """

    DISABLED = 'disabled'
    DEBUG = 'debug'
    ENABLED = 'enabled'
    CHOICES = (
        (DISABLED, '停用'),
        (DEBUG, '调试'),
        (ENABLED, '发行'),
    )
    VALUES = [x for x, _ in CHOICES]
    DICT = dict(CHOICES)

    @staticmethod
    def get():
        if current_user.is_authenticated() and current_user.debug \
                or hasattr(current_app, 'enable_debug') and current_app.enable_debug():
            return [Enable.ENABLED, Enable.DEBUG]
        return [Enable.ENABLED]


class Item(db.Document):
    """ 选项 """

    MENU_ICON = 'gear'

    TYPE_INT = 'int'
    TYPE_STRING = 'string'
    TYPE_CHOICES = (
        (TYPE_INT, '整数'),
        (TYPE_STRING, '字符'),
    )

    name = db.StringField(max_length=40, verbose_name='名称')
    key = db.StringField(max_length=40, verbose_name='键名')
    type = db.StringField(default=TYPE_INT, choices=TYPE_CHOICES, verbose_name='类型')
    value = db.DynamicField(verbose_name='值')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            'key',
            '-created',
        ]
    }

    @staticmethod
    def get(key, default=0, name=None):
        item = Item.objects(key=key).first()
        if item:
            return item.value

        Item(key=key, type=Item.TYPE_INT, value=default, name=name).save()
        return default

    @staticmethod
    def set(key, value, name=None):
        item = Item.objects(key=key).first()
        if not item:
            item = Item(key=key)

        if name:
            item.name = name
        item.type = Item.TYPE_INT
        item.value = value
        item.modified = datetime.now()
        item.save()

    @staticmethod
    def inc(key, default=0, num=1, name=None):
        query = dict(inc__value=num, set__modified=datetime.now())
        if name:
            query['set__name'] = name
        item = Item.objects(key=key).modify(**query)
        if not item:
            query = dict(key=key, type=Item.TYPE_INT, value=default + num)
            if name:
                query['name'] = name
            Item(**query).save()
            return default + num
        else:
            return item.value + num

    @staticmethod
    def data(key, default='', name=None):
        item = Item.objects(key=key).first()
        if item:
            return item.value

        Item(key=key, type=Item.TYPE_STRING, value=default, name=name).save()
        return default

    @staticmethod
    def set_data(key, value, name=None):
        item = Item.objects(key=key).first()
        if not item:
            item = Item(key=key)

        if name:
            item.name = name
        item.type = Item.TYPE_STRING
        item.value = value
        item.modified = datetime.now()
        item.save()


class Choice(db.EmbeddedDocument):
    """ 选项 """

    key = db.StringField(verbose_name='键名')
    name = db.StringField(verbose_name='名称')

    def __unicode__(self):
        return '%s - %s' % (self.key, self.name)


class Choices(db.Document):
    """ 选项模型 """

    MENU_ICON = 'plus-circle'

    fields = dict()
    key = db.StringField(verbose_name='键名')
    name = db.StringField(verbose_name='名称')
    default = db.StringField(verbose_name='默认值')
    choices = db.XListField(db.EmbeddedDocumentField(Choice), verbose_name='选项')
    enable = db.BooleanField(default=True, verbose_name='启用')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = dict(indexes=['key'])

    def __unicode__(self):
        return '%s - %s' % (self.key, self.name)

    @staticmethod
    def init():
        for key, field in Choices.fields.iteritems():
            Choices.init_field(key, field[1], field[0])

    @staticmethod
    def init_field(key, name, field, choices=None):
        choices = choices or Choices.objects(key=key).first()
        if choices:
            if choices.enable:
                if choices.default:
                    field.default = choices.default
                field.choices = [(x.key, x.name) for x in choices.choices]
            else:
                field.default = None
                field.choices = None
        else:
            Choices(key=key, name=name).save()
        Choices.refresh(field.owner_document)

    @staticmethod
    def refresh(model):
        if model:
            for admin in current_app.extensions.get('admin', []):
                for view in admin._views:
                    if model == getattr(view, 'model', None):
                        view._refresh_cache()

    def save(self):
        super(Choices, self).save()
        field = self.fields.get(self.key)
        if field:
            self.init_field(self.key, field[1], field[0], self)


def choice(field, key, name):
    Choices.fields[key] = (field, name)
    return field


db.dynamic = choice


class Share(db.EmbeddedDocument):
    """ 分享模型 """

    title = db.StringField(verbose_name='标题')
    content = db.StringField(verbose_name='描述')
    url = db.StringField(verbose_name='链接')
    image = db.StringField(verbose_name='图片链接')

    def __unicode__(self):
        url = self.url
        if current_user.is_authenticated() and url.strip():
            if url and '?' in url:
                url = '%s&uid=%d' % (url, current_user.id)
            else:
                url = '%s?uid=%d' % (url, current_user.id)

        return json.dumps(dict(
            title=self.title,
            content=self.content,
            url=url,
            image=self.image,
        ))

    @staticmethod
    def get(share, title='', content='', url='', image=''):
        if share:
            title = share.title or title
            content = share.content or content
            url = share.url or url
            image = share.image or image

        if current_user.is_authenticated() and url.strip():
            if url and '?' in url:
                url = '%s&uid=%d' % (url, current_user.id)
            else:
                url = '%s?uid=%d' % (url, current_user.id)

        return json.dumps(dict(
            title=title,
            content=content,
            url=url,
            image=image,
        ))


class StatLog(db.Document):
    """ 统计日志 """

    MENU_ICON = 'bar-chart'

    key = db.StringField(verbose_name='KEY')
    tid = db.StringField(verbose_name='TID')
    label = db.StringField(verbose_name='标签')
    day = db.StringField(verbose_name='日期')
    hour = db.IntField(default=0, verbose_name='小时')
    value = db.IntField(default=0, verbose_name='结果')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            '-created',
            ('key', 'tid'),
            ('key', 'tid', 'day', 'hour'),
        ]
    }

    @staticmethod
    def inc(key, tid, day=lambda: today(), hour=0, value=1):
        if callable(day):
            day = day()
        day = str(day)[:10]
        item = StatLog.objects(key=key, tid=tid, day=day).modify(
            inc__value=value,
            set__modified=datetime.now(),
        )
        if not item:
            StatLog(key=key, tid=tid, day=day, hour=0, value=value).save()
            return value
        else:
            return item.value + 1

    @staticmethod
    def get(key, tid, day=today(), hour=0, default=0, save=True):
        if callable(day):
            day = day()
        day = str(day)[:10]
        item = StatLog.objects(key=key, tid=tid, day=day).first()
        if item:
            return item.value

        if save:
            StatLog(key=key, tid=tid, day=day, hour=0, value=default).save()
        return default

    @staticmethod
    def date_inc(key, tid='', label='', value=1, day=None):
        day = time.strftime('%Y-%m-%d') if not day else day
        doc = {'$inc':{'value':value}, '$set':{'modified':datetime.now()}, '$setOnInsert':{'created': datetime.now()}}
        log = StatLog.objects(key=str(key), tid=tid, label=label, day=day, hour=-1).update_one(__raw__=doc, upsert=True)
        return StatLog.date_get(key, tid=tid, label=label, day=day)

    @staticmethod
    def date_get(key, tid='', label='', day=None):
        day = time.strftime('%Y-%m-%d') if not day else day
        log = StatLog.objects(key=str(key), tid=tid, label=label, day=day, hour=-1).first()
        return log.value if log else 0


class TraceLog(db.Document):
    """ 监控统计 """

    MENU_ICON = 'bug'

    key = db.StringField(verbose_name='KEY')
    tid = db.StringField(verbose_name='TID')
    user = db.IntField(verbose_name='用户')
    label = db.StringField(verbose_name='标识')
    value = db.StringField(verbose_name='结果')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            'key',
            'tid',
            'label',
            '-created',
        ]
    }


class Channel(db.Document):
    """ 渠道模型 """

    MENU_ICON = 'road'

    id = db.IntField(primary_key=True, verbose_name='ID')
    name = db.StringField(max_length=40, verbose_name='名称')
    password = db.StringField(max_length=40, verbose_name='密码')
    desc = db.StringField(verbose_name='描述')
    url = db.StringField(verbose_name='链接')
    image = db.XImageField(verbose_name='二维码')
    active = db.BooleanField(default=True, verbose_name='激活')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            '-created',
        ]
    }

    def is_user(self):
        return True

    def is_authenticated(self):
        """ 是否登录 """
        return True

    def is_active(self):
        """ 是否激活 """
        return True

    def is_anonymous(self):
        """ 是否游客 """
        return False

    def get_id(self):
        """ 获取用户ID """
        return '%s:%s' % ('channel', str(self.id))

    def create(self):
        """ 创建渠道 """
        if not self.id:
            self.id = Item.inc('channel_index', 1000)
            self.save()
        return self.id


class AndroidVersion(db.Document):
    """ 安卓版本 """

    MENU_ICON = 'android'

    id = db.IntField(primary_key=True, verbose_name='ID')
    version = db.StringField(max_length=200, verbose_name='版本')
    log = db.StringField(verbose_name='更新日志')
    url = db.StringField(verbose_name='应用地址')
    force = db.StringField(verbose_name='强制更新')
    enable = db.StringField(default=Enable.ENABLED, verbose_name='状态', choices=Enable.CHOICES)
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            '-created',
        ]
    }

    def __unicode__(self):
        return '%d - %s' % (self.id, self.version)

    def create(self):
        """ 创建版本 """
        if not self.id:
            self.id = Item.inc('android_version_index', 100)
            self.save()
        return self.id


class IOSVersion(db.Document):
    """ IOS版本 """

    MENU_ICON = 'mobile'

    id = db.IntField(primary_key=True, verbose_name='ID')
    version = db.StringField(max_length=200, verbose_name='版本')
    log = db.StringField(verbose_name='更新日志')
    url = db.StringField(verbose_name='应用地址')
    force = db.StringField(verbose_name='强制更新')
    enable = db.StringField(default=Enable.ENABLED, verbose_name='状态', choices=Enable.CHOICES)
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            '-created',
        ]
    }

    def __unicode__(self):
        return '%d - %s' % (self.id, self.version)

    def create(self):
        """ 创建版本 """
        if not self.id:
            self.id = Item.inc('ios_version_index', 100)
            self.save()
        return self.id


class API(db.Document):
    """ 接口模型 """

    MENU_ICON = 'server'

    name = db.StringField(verbose_name='名称')
    key = db.StringField(verbose_name='键名')
    url = db.StringField(verbose_name='链接')
    expire = db.IntField(default=0, verbose_name='缓存')
    cache = db.BooleanField(verbose_name='已缓存')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            '-created',
        ]
    }

    @property
    def detail(self):
        return dict(
            name=self.name,
            key=self.key,
            url=self.url,
            expire=self.expire,
            cache=self.cache,
        )


class Icon(db.Document):
    """ 图标模型 """

    MENU_ICON = 'picture-o'

    key = db.StringField(verbose_name='ID')
    icon = db.Base64ImageField(verbose_name='图标')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            '-created',
        ]
    }


class Action(db.Document):
    """ 功能模型 """

    MENU_ICON = 'bars'

    key = db.StringField(verbose_name='ID')
    name = db.StringField(verbose_name='名称')
    desc = db.StringField(verbose_name='描述')
    icon = db.Base64ImageField(verbose_name='图标')
    active_icon = db.Base64ImageField(verbose_name='激活图标')
    module = choice(db.StringField(verbose_name='模块'), 'action_module', '功能模块')
    data = db.StringField(verbose_name='数据')
    target = db.StringField(verbose_name='目标')
    share = db.EmbeddedDocumentField(Share, verbose_name='分享')
    sort = db.IntField(verbose_name='排序')
    android_start = db.ReferenceField(AndroidVersion, verbose_name='安卓版本')
    android_end = db.ReferenceField(AndroidVersion, verbose_name='安卓最大版本')
    ios_start = db.ReferenceField(IOSVersion, verbose_name='IOS版本')
    ios_end = db.ReferenceField(IOSVersion, verbose_name='IOS最大版本')
    login = db.BooleanField(default=False, verbose_name='登陆')
    login_show = db.BooleanField(default=False, verbose_name='登陆显示')
    debug = db.BooleanField(default=False, verbose_name='调试')
    enable = db.StringField(default=Enable.ENABLED, verbose_name='状态', choices=Enable.CHOICES)
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            'key',
            'sort',
            '-created',
        ]
    }

    @property
    def detail(self):
        return dict(
            id=self.key,
            name=self.name,
            desc=self.desc,
            icon=self.icon.base64,
            active_icon=self.active_icon.base64,
            data=self.data,
            target=self.target,
            share=unicode(self.share),
            login=self.login,
            login_show=self.login_show,
            debug=self.debug,
        )


class TPL(db.Document):
    """ 模板模型 """

    MENU_ICON = 'globe'

    name = db.StringField(verbose_name='名称')
    key = db.StringField(verbose_name='键名')
    tpl = db.XFileField(verbose_name='文件', allows=['html', 'htm'])
    enable = db.StringField(default=Enable.ENABLED, verbose_name='状态', choices=Enable.CHOICES)
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')


class Slide(db.Document):
    """ 广告模型 """

    MENU_ICON = 'paw'

    key = db.StringField(verbose_name='ID')
    name = db.StringField(verbose_name='名称')
    icon = db.XImageField(verbose_name='图标')
    module = choice(db.StringField(verbose_name='模块'), 'slide_module', '广告模块')
    target = db.StringField(verbose_name='目标')
    share = db.EmbeddedDocumentField(Share, verbose_name='分享')
    sort = db.IntField(verbose_name='排序')
    android_start = db.ReferenceField(AndroidVersion, verbose_name='安卓版本')
    android_end = db.ReferenceField(AndroidVersion, verbose_name='安卓最大版本')
    ios_start = db.ReferenceField(IOSVersion, verbose_name='IOS版本')
    ios_end = db.ReferenceField(IOSVersion, verbose_name='IOS最大版本')
    login = db.BooleanField(default=False, verbose_name='登陆')
    enable = db.StringField(default=Enable.ENABLED, verbose_name='状态', choices=Enable.CHOICES)
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            'key',
            'sort',
            '-created',
        ]
    }

    @property
    def detail(self):
        return dict(
            id=self.key,
            name=self.name,
            icon=self.icon.link,
            target=self.target,
            share=unicode(self.share),
            login=self.login,
            login_show=self.login_show,
            debug=self.debug,
        )


class UserImage(db.Document):
    """ 用户图片 """

    MENU_ICON = 'picture-o'

    user = db.IntField(verbose_name='用户')
    source = db.StringField(verbose_name='来源')
    image = db.XImageField(config='USER_IMAGES', verbose_name='图片')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            'source',
            '-created',
        ]
    }


class ImageItem(db.Document):
    """ 图片模型 """

    MENU_ICON = 'picture-o'

    image = db.XImageField(verbose_name='图片')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')


class Option(db.Document):
    """ 配置模型 """

    MENU_ICON = 'gear'

    name = db.StringField(verbose_name='名称')
    key = db.StringField(verbose_name='键名')
    value = db.StringField(verbose_name='值')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = dict(indexes=['-created'])


class Menu(db.Document):
    """ 菜单模型 """

    MENU_ICON = 'sitemap'

    key = db.StringField(verbose_name='键名')
    name = db.StringField(verbose_name='名称')
    link = db.StringField(verbose_name='链接')
    icon = db.XImageField(verbose_name='图标')
    module = choice(db.StringField(verbose_name='模块'), 'menu_module', '菜单模块')
    sort = db.IntField(verbose_name='排序')
    enable = db.StringField(default=Enable.ENABLED, verbose_name='状态', choices=Enable.CHOICES)
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = dict(indexes=[('enable', 'module', 'sort')])

    @staticmethod
    def get(module):
        return Menu.objects(module=module, enable=Enable.get()).order_by('sort')


class Page(db.Document):
    """ 网页模型 """

    MENU_ICON = 'globe'

    id = db.IntField(primary_key=True, verbose_name='ID')
    key = db.StringField(verbose_name='键名')
    bg = db.StringField(verbose_name='背景颜色(#FFF)')
    name = db.StringField(verbose_name='名称')
    content = db.StringField(verbose_name='正文')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = dict(indexes=['-created'])

    def create(self):
        """ 创建用户 """
        if not self.id:
            self.id = Item.inc('page_index', 1000)
            self.save()
        return self.id


class Field(db.EmbeddedDocument):
    """ 选项 """

    TYPE_INT = 'IntField'
    TYPE_STRING = 'StringField'
    TYPE_REF = 'ReferenceField'
    TYPE_IMAGE = 'XImageField'
    TYPE_FILE = 'XFileField'
    TYPE_DATETIME = 'DateTimeField'
    TYPE_BOOL = 'BooleanField'
    TYPE_CHOICES = [
        (TYPE_INT, TYPE_INT),
        (TYPE_STRING, TYPE_STRING),
        (TYPE_REF, TYPE_REF),
        (TYPE_IMAGE, TYPE_IMAGE),
        (TYPE_FILE, TYPE_FILE),
        (TYPE_DATETIME, TYPE_DATETIME),
        (TYPE_BOOL, TYPE_BOOL),
    ]

    key = db.StringField(max_length=100, verbose_name='键名')
    type = db.StringField(default=TYPE_INT, choices=TYPE_CHOICES, verbose_name='类型')
    name = db.StringField(max_length=100, verbose_name='名称')
    default = db.StringField(max_length=100, verbose_name='默认值')
    model = db.ReferenceField('Model', verbose_name='引用')
    choices = db.ReferenceField('Choices', verbose_name='选项')

    def __unicode__(self):
        return '%s - %s' % (self.key, self.name)


class Model(db.Document):
    """ 建模 """

    MENU_ICON = 'database'

    name = db.StringField(max_length=100, verbose_name='名称')
    desc = db.StringField(max_length=100, verbose_name='描述')
    fields = db.XListField(db.EmbeddedDocumentField(Field), verbose_name='字段')
    modified_field = db.BooleanField(default=True, verbose_name='修改')
    created_field = db.BooleanField(default=True, verbose_name='创建')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    def __unicode__(self):
        return self.name


class View(db.Document):
    """ 管理 """

    MENU_ICON = 'futbol-o'

    TYPE_VIEW = 'view'
    TYPE_MODEL = 'model'
    TYPE_CATE = 'cate'
    TYPE_CHOICES = [
        (TYPE_VIEW, '默认'),
        (TYPE_MODEL, '模型'),
        (TYPE_CATE, '分类'),
    ]

    name = db.StringField(max_length=100, verbose_name='名称')
    label = db.StringField(max_length=100, verbose_name='标识')
    type = db.StringField(default=TYPE_VIEW, choices=TYPE_CHOICES, verbose_name='类型')
    model = db.ReferenceField('Model', verbose_name='模型')
    icon = db.StringField(max_length=100, verbose_name='图标')
    page_size = db.IntField(default=50, verbose_name='分页数')
    can_create = db.BooleanField(default=True, verbose_name='能创建')
    can_edit = db.BooleanField(default=True, verbose_name='能修改')
    can_delete = db.BooleanField(default=True, verbose_name='能删除')
    column_default_sort = db.StringField(max_length=100, verbose_name='默认排序')
    column_list = db.ListField(db.StringField(), verbose_name='显示列表')
    column_center_list = db.ListField(db.StringField(), verbose_name='居中列表')
    column_hidden_list = db.ListField(db.StringField(), verbose_name='隐藏列表')
    column_filters = db.ListField(db.StringField(), verbose_name='过滤器列表')
    column_sortable_list = db.ListField(db.StringField(), verbose_name='排序列表')
    column_searchable_list = db.ListField(db.StringField(), verbose_name='查找列表')
    form_excluded_columns = db.ListField(db.StringField(), verbose_name='表单隐藏列表')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    def __unicode__(self):
        return self.name

    def setup(self, admin, view):
        view.name = self.label or view.name
        view.menu_icon_value = self.icon or view.menu_icon_value
        if hasattr(view, 'model'):
            if not view.menu_icon_value:
                if view.model and hasattr(view.model, 'MENU_ICON'):
                    view.menu_icon_value = view.model.MENU_ICON
                else:
                    view.menu_icon_value = 'file-o'
            view.page_size = self.page_size or view.page_size
            view.can_create = self.can_create
            view.can_edit = self.can_edit
            view.can_delete = self.can_delete
            if self.column_default_sort:
                try:
                    view.column_default_sort = json.loads(self.column_default_sort)
                except:
                    pass
            view.column_list = self.column_list or view.column_list
            view.column_center_list = self.column_center_list or getattr(view, 'column_center_list', None)
            view.column_hidden_list = self.column_hidden_list or getattr(view, 'column_hidden_list', None)
            view.column_filters = self.column_filters or view.column_filters
            view.column_sortable_list = self.column_sortable_list or view.column_sortable_list
            view.column_searchable_list = self.column_searchable_list or view.column_searchable_list
            view.form_excluded_columns = self.form_excluded_columns or view.form_excluded_columns
            view._refresh_cache()
        elif not view.menu_icon_value:
            if hasattr(view, 'MENU_ICON'):
                view.menu_icon_value = view.MENU_ICON
        admin._refresh()

    def save(self):
        super(View, self).save()

        if current_app.cool_manager and not current_app.cool_manager.loading:
            for admin in current_app.extensions.get('admin', []):
                for view in admin._views:
                    if view.__class__.__name__ == self.name:
                        self.setup(admin, view)
                        break

    def add_text(self, key):
        attr = getattr(self, key)
        if attr:
            return '    %s = %s' % (key, json.dumps(attr))

    @property
    def code_text(self):
        texts = []
        keys = ['column_list', 'column_center_list', 'column_hidden_list',
            'column_filters', 'column_sortable_list', 'column_searchable_list',
            'form_excluded_columns']
        for key in keys:
            text = self.add_text(key)
            if text:
                texts.append(text)
        return '\n'.join(texts)


class IP(db.Document):
    """ IP名单 """

    MENU_ICON = 'wifi'
    TYPE = db.choices(register='注册', sms='短信')

    ip = db.StringField(verbose_name='IP')
    type = db.StringField(default=TYPE.REGISTER, choices=TYPE.CHOICES, verbose_name='类型')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = dict(indexes=['-created', ('type', 'ip')])

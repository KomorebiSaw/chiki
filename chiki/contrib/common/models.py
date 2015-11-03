# coding: utf-8
import json
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
        if current_user.is_authenticated() and current_user.debug == True \
                or hasattr(current_app, 'enable_debug') and current_app.enable_debug():
            return [Enable.ENABLED, Enable.DEBUG]
        return [Enable.ENABLED]


class Action(object):
    """ 动作选项 """

    DEFAULT = 'default'
    EMPTY = 'empty'
    TABLIST = 'tablist'
    WEBSTATIC = 'webstatic'
    WEBVIEW = 'webview'
    LISTVIEW = 'listview'
    GRIDVIEW = 'gridview'
    BROWSER = 'browser'
    REDIRECT = 'redirect'
    DIVIDER = 'divider'
    CHOICES = (
        (DEFAULT, '原生'),
        (EMPTY, '无动作'),
        (TABLIST, 'Tab'),
        (WEBSTATIC, '静态网页'),
        (WEBVIEW, '网页'),
        (LISTVIEW, '列表'),
        (GRIDVIEW, '表格'),
        (BROWSER, '浏览器'),
        (REDIRECT, '内部跳转'),
        (DIVIDER, '分割线'),
    )
    VALUES = [x[0] for x in CHOICES]
    DICT = dict(CHOICES)


class Item(db.Document):
    """ 通用选项 """

    TYPE_INT = 'int'
    TYPE_STRING = 'string'
    TYPE_CHOICES = (
        (TYPE_INT, '整数'),
        (TYPE_STRING, '字符'),
    )

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
    def get(key, default=0):
        item = Item.objects(key=key).first()
        if item:
            return item.value
            
        Item(key=key, type=Item.TYPE_INT, value=default).save()
        return default

    @staticmethod
    def set(key, value):
        item = Item.objects(key=key).first()
        if not item:
            item = Item(key=key)

        item.type = Item.TYPE_INT
        item.value = value
        item.modified = datetime.now()
        item.save()

    @staticmethod
    def inc(key, default=0):
        item = Item.objects(key=key).modify(
            inc__value=1, 
            set__modified=datetime.now(),
        )
        if not item:
            Item(key=key, type=Item.TYPE_INT, value=default + 1).save()
            return default + 1
        else:
            return item.value + 1

    @staticmethod
    def data(key, default=''):
        item = Item.objects(key=key).first()
        if item:
            return item.value

        Item(key=key, type=Item.TYPE_STRING, value=default).save()
        return default

    @staticmethod
    def set_data(key, value):
        item = Item.objects(key=key).first()
        if not item:
            item = Item(key=key)

        item.type = Item.TYPE_STRING
        item.value = value
        item.modified = datetime.now()
        item.save()


class ShareItem(db.EmbeddedDocument):
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
    key = db.StringField(verbose_name='KEY')
    tid = db.StringField(verbose_name='TID')
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


class TraceLog(db.Document):
    """ 监控统计 """

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

    id = db.IntField(primary_key=True, verbose_name='ID')
    name = db.StringField(max_length=40, verbose_name='名称')
    desc = db.StringField(verbose_name='描述')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            '-created',
        ]
    }

    def create(self):
        """ 创建渠道 """
        if not self.id:
            self.id = Item.inc('channel_index', 1000)
            self.save()
        return self.id


class AndroidVersion(db.Document):
    """ 安卓版本 """

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


class APIItem(db.Document):
    """ 接口模型 """

    name = db.StringField(verbose_name='名称')
    key = db.StringField(verbose_name='键名')
    url = db.StringField(verbose_name='链接')
    cache = db.IntField(default=0, verbose_name='缓存')
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
            cache=self.cache,
        )


class UserImage(db.Document):
    """ 用户图片 """

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


class ActionItem(db.Document):
    """ 功能模型 """

    DEFAULT = 'default'
    MODULE_CHOICES = (
        (DEFAULT, '默认')
    )
    MODULE_VALUES = [x[0] for x in MODULE_CHOICES]

    name = db.StringField(verbose_name='名称')
    key = db.StringField(verbose_name='键名')
    icon = db.XImageField(verbose_name='图标')
    module = db.StringField(default=DEFAULT, verbose_name='模块', choices=MODULE_CHOICES)
    action = db.StringField(default=Action.DEFAULT, verbose_name='动作', choices=Action.CHOICES)
    url = db.StringField(verbose_name='链接')
    share = db.EmbeddedDocumentField(ShareItem, verbose_name='分享')
    sort = db.IntField(verbose_name='排序')
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
            name=self.name,
            key=self.key,
            icon=self.icon.link,
            action=self.action,
            login=self.login,
            url=self.url,
            share=unicode(self.share),
        )


class TPLItem(db.Document):
    """ 模板模型 """

    name = db.StringField(verbose_name='名称')
    key = db.StringField(verbose_name='键名')
    tpl = db.XFileField(verbose_name='文件', allows=['html', 'htm'])
    enable = db.StringField(default=Enable.ENABLED, verbose_name='状态', choices=Enable.CHOICES)
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')


class SlideItem(db.Document):
    """ 广告模型 """

    MODULE_HEAD = 'home_head'
    MODULE_FOOT = 'home_foot'
    MODULE_CHOICES = (
        (MODULE_HEAD, '头部'),
        (MODULE_FOOT, '底部'),
    )

    name = db.StringField(verbose_name='名称')
    image = db.XImageField(verbose_name='图片')
    module = db.StringField(default=MODULE_HEAD, verbose_name='模块', choices=MODULE_CHOICES)
    action = db.StringField(default=Action.DEFAULT, verbose_name='动作', choices=Action.CHOICES)
    url = db.StringField(verbose_name='链接')
    share = db.EmbeddedDocumentField(ShareItem, verbose_name='分享')
    sort = db.IntField(verbose_name='排序')
    enable = db.StringField(default=Enable.ENABLED, verbose_name='状态', choices=Enable.CHOICES)
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            'sort',
            '-created',
        ]
    }

    @property
    def detail(self):
        return dict(
            name=self.name,
            icon=self.image.link,
            action=self.action,
            url=self.url,
            share=unicode(self.share),
        )

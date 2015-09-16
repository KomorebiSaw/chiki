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
    def get(key, tid, day=today(), hour=0, default=0):
        if callable(day):
            day = day()
        day = str(day)[:10]
        item = StatLog.objects(key=key, tid=tid, day=day).first()
        if item:
            return item.value
            
        StatLog(key=key, tid=tid ,day=day, hour=0, value=default).save()
        return default
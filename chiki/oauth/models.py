#coding: utf-8
from chiki.base import db
from datetime import datetime


class Second(db.EmbeddedDocument):
    """ 二级菜单 """

    name = db.StringField(verbose_name='标题')
    url = db.StringField(verbose_name='链接')

    def __unicode__(self):
        return '%s-%s' % (self.name, self.url)


class WXMenu(db.Document):

    name = db.StringField(verbose_name='主菜单')
    second = db.ListField(db.EmbeddedDocumentField(Second), verbose_name='二级菜单')
    url = db.StringField(verbose_name='链接')
    sort = db.IntField(verbose_name='排序')
    make = db.BooleanField(verbose_name='使用', default=False)
    created = db.DateTimeField(verbose_name='创建时间', default=datetime.now)

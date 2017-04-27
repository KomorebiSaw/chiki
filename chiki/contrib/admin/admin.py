# coding: utf-8
from chiki.admin import ModelView


class AdminUserView(ModelView):
    """ 管理员 """

    column_center_list = ('username', 'password', 'root', 'active', 'logined',
                          'modified', 'created')


class GroupView(ModelView):
    """ 管理组 """

    column_center_list = ('name', 'modified', 'created')

    def __unicode__(self):
        return self.name

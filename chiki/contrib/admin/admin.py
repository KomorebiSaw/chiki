# coding: utf-8
from chiki.admin import ModelView


class AdminUserView(ModelView):
    """ 管理员 """
    # can_edit = False
    # can_delete = False
    column_list = ('username', 'root', 'active', 'logined',
                   'modified', 'created', 'group')
    column_center_list = column_list


class GroupView(ModelView):
    """ 管理组 """
    column_center_list = ('name', 'modified', 'created')

    form_args = dict(
        power=dict(allow_blank=True),
        can_create=dict(allow_blank=True),
        can_edit=dict(allow_blank=True),
        can_delete=dict(allow_blank=True),
    )

    def __unicode__(self):
        return self.name


class AdminUserLoginLogView(ModelView):
    """ 管理登录日志 """

    can_edit = False
    can_delete = False
    column_center_list = ('user', 'type', 'spm', 'ip', 'created')

    def __unicode__(self):
        return '管理员登陆日志(%s)' % self.id


class AdminChangeLogView(ModelView):
    """ 管理员操作日志 """

    can_delete = False
    can_edit = False
    column_center_list = ('user', 'type', 'created')

    def __unicode__(self):
        return '管理员操作日志(%s)' % self.id

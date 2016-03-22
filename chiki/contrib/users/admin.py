# coding: utf-8
from chiki.admin import ModelView
from datetime import datetime


class UserView(ModelView):
    show_popover = True
    column_default_sort = ('registered', True)
    column_list = (
        'id', 'phone', 'avatar', 'location', 'debug', 'active', 'channel', 'spm', 'ip',
        'generate', 'error', 'logined', 'registered'
    )
    column_center_list = (
        'id', 'phone', 'avatar', 'debug', 'active', 'channel', 'spm', 'ip',
        'generate', 'error', 'logined', 'registered'
    )
    column_searchable_list = ('phone',)
    column_filters = ('id', 'phone',)
    form_excluded_columns = ('id', 'generate')

    def on_model_change(self, form, model, created=False):
        model.create()
        if created:
            model.generate = True
        model.modified = datetime.now()


class WeChatUserView(ModelView):
    show_popover = True
    column_default_sort = ('created', True)
    column_list = (
        'user', 'scene', 'nickname', 'province', 'city', 'privilege', 'subscribe', 'subscribe_time', 'remark', 'groupid', 'access_token', 
        'expires_in', 'refresh_token', 'updated', 'modified', 'created'
    )
    column_center_list = (
        'user', 'nickname', 'province', 'city', 'privilege', 'subscribe', 'subscribe_time', 'remark', 'groupid', 'access_token', 
        'expires_in', 'refresh_token', 'updated', 'modified', 'created'
    )
    column_searchable_list = ('unionid', 'mp_openid', )
    column_filters = ('user',)


class QQUserView(ModelView):
    show_popover = True
    column_default_sort = ('created', True)
    column_list = ('user', 'openid', 'is_yellow_vip', 'is_yellow_year_vip', 'access_token' ,'expires_in', 'refresh_token', 'modified', 'created')
    column_center_list = ('user', 'openid', 'is_yellow_vip', 'is_yellow_year_vip', 'access_token' ,'expires_in', 'refresh_token', 'modified', 'created')
    column_searchable_list = ('openid',)
    column_filters = ('openid', 'is_yellow_vip', 'vip', 'yellow_vip_level', 'level', 'is_yellow_year_vip')


class WeiBoUser(ModelView):
    show_popover = True
    column_default_sort = ('created', True)
    column_list = ('user', 'uid', 'subscribe', 'subscribe_time', 'follow', 'access_token', 'expires_in', 'refresh_token', 'modified', 'created')
    column_center_list = ('user', 'uid', 'subscribe', 'subscribe_time', 'follow', 'access_token', 'expires_in', 'refresh_token', 'modified', 'created')
    column_searchable_list = ('province', 'city',)
    column_filters = ('user', 'uid')



class UserLogView(ModelView):
    pass


class PhoneCodeView(ModelView):
    pass


class EmailCodeView(ModelView):
    pass

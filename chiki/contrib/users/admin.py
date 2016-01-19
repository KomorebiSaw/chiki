# coding: utf-8
from chiki.admin import ModelView


class UserView(ModelView):
    show_popover = True
    column_default_sort = ('created', True)
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


class WeChatUserView(ModelView):
    show_popover = True
    column_default_sort = ('created', True)
    column_list = (
        'user', 'mobile_openid', 'headimgurl', 'privilege', 'subscribe', 'subscribe_time', 'remark', 'groupid', 'access_token', 
        'expires_in', 'refresh_token', 'updated', 'modified', 'created'
    )
    column_center_list = (
        'user', 'mobile_openid', 'headimgurl', 'privilege', 'subscribe', 'subscribe_time', 'remark', 'groupid', 'access_token', 
        'expires_in', 'refresh_token', 'updated', 'modified', 'created'
    )
    column_hidden_list = ('headimgurl',)
    column_searchable_list = ('unionid', 'mp_openid', 'mobile_openid',)
    column_filters = ('user', 'mobile_openid')


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

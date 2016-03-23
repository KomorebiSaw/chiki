# coding: utf-8
import hashlib
from chiki import is_json
from chiki.api import abort
from chiki.api.const import *
from chiki.contrib.common import Item
from chiki.web import error
from flask import flash, render_template, redirect, url_for, current_app
from flask.ext.login import login_user, current_user

__all__ = [
    'init_wxauth', 'get_wechat_user', 'create_wechat_user',
    'wechat_login', 'on_wechat_login',
]


def get_wechat_user(access):
    um = current_app.user_manager
    config = current_app.config.get('WXAUTH')
    if len(config) > 1:
        return um.models.WeChatUser(unionid=access['unionid']).first()
    query = {'%s_openid' % config.items()[0][0]: access['openid']}
    return um.models.WeChatUser.objects(**query).first()


def create_wechat_user(userinfo, action):
    um = current_app.user_manager
    return um.models.WeChatUser.create(userinfo, action)


def wechat_login(wxuser):
    um = current_app.user_manager
    model = um.config.oauth_model
    if model == 'auto' and not wxuser.user:
        um.models.User.from_wechat(wxuser)


def on_wechat_login(action, next):
    pass


def init_wxauth(app):
    if not hasattr(app, 'wxauth'):
        return

    wxauth = app.wxauth
    um = app.user_manager

    @wxauth.success_handler
    def wxauth_success(action, scope, access, next):
        user = um.funcs.get_wechat_user(access)
        if not user:
            if wxauth.SNSAPI_USERINFO not in access['scope'] \
                    and wxauth.SNSAPI_LOGIN not in access['scope']:
                return wxauth.auth(action, next, wxauth.SNSAPI_USERINFO)

            userinfo = wxauth.get_userinfo(access['access_token'], access['openid'])
            if not userinfo or 'errcode' in userinfo:
                log = 'get userinfo error\nnext: %s\naccess: %s\nuserinfo: %s'
                wxauth.app.logger.error(log % (next, str(access), str(userinfo)))
                return wxauth.error(wxauth.GET_USERINFO_ERROR, action, next)

            user = um.funcs.create_wechat_user(userinfo, action)

        um.funcs.wechat_login(user)

        if user.user:
            user = um.models.User.objects(id=user.user).first() or user

        login_user(user, remember=True)
        if current_user.is_authenticated() and current_user.is_user():
            user.login()

        return um.funcs.on_wechat_login(action, next)

    @wxauth.error_handler
    def wxauth_error(err, action, next):
        if is_json():
            abort(WXAUTH_ERROR, wxcode=err, wxmsg=wxauth.MSGS.get(err, '未知错误'))

        return error('微信授权失败')

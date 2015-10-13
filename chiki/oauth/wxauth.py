# coding: utf-8
import json
import time
import requests
import werobot.client
from urllib import quote, urlencode
from flask import current_app, request, redirect, url_for
from chiki.api import abort, success
from chiki.api.const import *
from chiki.utils import err_logger, is_json, is_api
from chiki.oauth.jssdk import JSSDK

__all__ = [
    'WXAuth', 'init_wxauth',
]


class WXAuth(object):

    ACTION_MP = 'mp'
    ACTION_MOBILE = 'mobile'
    ACTION_QRCODE = 'qrcode'

    ARGS_ERROR = 'args_error'
    AUTH_ERROR = 'auth_error'
    ACCESS_ERROR = 'access_error'
    GET_USERINFO_ERROR = 'get_userinfo_error'
    MSGS = {
        ARGS_ERROR: '参数错误',
        AUTH_ERROR: '授权失败',
        ACCESS_ERROR: '获取令牌失败',
        GET_USERINFO_ERROR: '获取用户信息失败',
    }

    SNSAPI_BASE = 'snsapi_base'
    SNSAPI_USERINFO = 'snsapi_userinfo'
    AUTH_CONNECT_URL = 'https://open.weixin.qq.com/connect/oauth2/authorize'
    AUTH_QRCONNECT_URL = 'https://open.weixin.qq.com/connect/qrconnect'
    ACCESS_URL = 'https://api.weixin.qq.com/sns/oauth2/access_token'
    REFRESH_URL = 'https://api.weixin.qq.com/sns/oauth2/refresh_token'
    USERINFO_URL = 'https://api.weixin.qq.com/sns/userinfo'
    CHECK_URL = 'https://api.weixin.qq.com/sns/auth'

    def __init__(self, app=None):
        self.success_callback = None
        self.error_callback = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.config = app.config.get('WXAUTH')
        mp = self.config.get(self.ACTION_MP)
        self.client = werobot.client.Client(mp.get('appid'), mp.get('secret'))
        app.wxauth = self
        app.wxclient = self.client

        @app.route(self.config.get('wxauth_url', '/oauth/wechat/callback'))
        def wxauth_callback():
            return self.callback()

        app.jssdk = JSSDK(app)

    def quote(self, **kwargs):
        return dict((x, quote(y)) for x, y in kwargs.iteritems())

    def get_access_url(self, action, code):
        config = self.config.get(action)
        query = dict(
            appid=config.get('appid'),
            secret=config.get('secret'),
            code=code,
            grant_type='authorization_code',
        )
        return '%s?%s' % (self.ACCESS_URL, urlencode(query))

    @err_logger
    def access_token(self, action, code):
        url = self.get_access_url(action, code)
        return requests.get(url).json()

    def get_refresh_url(self, action, token):
        config = self.config.get(action)
        query = dict(
            appid=config.get('appid'),
            refresh_token=token,
            grant_type='refresh_token',
        )
        return '%s?%s' % (self.REFRESH_URL, urlencode(query))

    @err_logger
    def refresh_token(self, action, token):
        url = self.get_refresh_url(action, token)
        return requests.get(url).json()

    def get_userinfo_url(self, token, openid, lang='zh_CN'):
        query = dict(access_token=token, openid=openid, lang=lang)
        return '%s?%s' % (self.USERINFO_URL, urlencode(query))

    @err_logger
    def get_userinfo(self, token, openid):
        url = self.get_userinfo_url(token, openid)
        res = requests.get(url)
        return json.loads(res.content)

    @err_logger
    def get_user_info(self, openid):
        return self.client.get_user_info(openid)

    def get_check_url(self, token, openid):
        query = dict(access_token=token, openid=openid)
        return '%s?%s' % (self.CHECK_URL, urlencode(query))

    @err_logger
    def check_token(self, token, openid):
        url = self.get_check_url(token, openid)
        return requests.get(url).json()['errcode'] == 0

    def get_auth_url(self, action, next, scope=SNSAPI_BASE, state='STATE'):
        config = self.config.get(action)
        query = self.quote(
            appid=config.get('appid'),
            callback=url_for('wxauth_callback', scope=scope, next=next, action=action, _external=True),
            scope=scope,
            state=state,
        )
        url = self.AUTH_CONNECT_URL if action == 'mp' else self.AUTH_QRCONNECT_URL
        return '{url}?appid={appid}&redirect_uri={callback}&response_type=code' \
            '&scope={scope}&state={state}#wechat_redirect'.format(url=url, **query)

    def get_action(self, action):
        if not action:
            ua = request.headers.get('User-Agent', '').lower()
            if 'micromessenger' in ua:
                action = self.ACTION_MP
            elif is_api():
                action = self.ACTION_MOBILE
            else:
                action = self.ACTION_QRCODE
        return action

    def auth(self, action='', next='', scope=SNSAPI_BASE, state='STATE'):
        action = self.get_action(action)
        if action == 'mobile' or is_json():
            return abort(WXAUTH_REQUIRED)

        return redirect(self.get_auth_url(action, next, scope, state))

    def callback(self):
        action = request.args.get('action', 'mp')
        code = request.args.get('code', '')
        next = request.args.get('next', '')
        scope = request.args.get('scope', self.SNSAPI_BASE)

        if action not in ['mp', 'mobile', 'qrcode']:
            return self.error(self.ARGS_ERROR, action, next)

        if not code:
            return self.error(self.AUTH_ERROR, action, next)

        access = self.access_token(code)
        if not access or 'openid' not in access:
            log = 'access error\nnext: %s\ncode: %s\naccess: %s'
            current_app.logger.error(log % (next, code, str(access)))
            return self.error(self.ACCESS_ERROR, action, next)

        return self.success(action, scope, access, next)

    def success(self, action, scope, access, next):
        callback = self.success_callback
        if not callback:
            return '授权成功，请设置回调'

        res = callback(action, scope, access, next)
        return res if res else (success() if is_json() else redirect(next))

    def error(self, err, action, next):
        res = '授权失败(%s): %s' % (action, err)
        if self.error_callback:
            res = self.error_callback(err, action, next) or res
        return res

    def success_handler(self, callback):
        self.success_callback = callback
        return callback

    def error_handler(self, callback):
        self.error_callback = callback
        return callback


def init_wxauth(app):
    if app.config.get('WXAUTH'):
        return WXAuth(app)

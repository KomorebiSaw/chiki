# coding: utf-8
import json
import time
import requests
import werobot.client
from urllib import quote, urlencode
from flask import current_app, request, redirect, url_for
from chiki.jssdk import JSSDK
from chiki.utils import err_logger
from chiki.contrib.common import Item

__all__ = [
    'WXAuth', 'init_wxauth',
]


@property
def common_token(self):
    now = time.time()
    key = 'wxauth:access_token'
    token = json.loads(Item.data(key, '{}'))
    if not token or token['deadline'] <= now:
        token = self.grant_token()
        token['deadline'] = now + token['expires_in']
        Item.set_data(key, json.dumps(token))
    return token['access_token']

werobot.client.Client.token = common_token


class WXAuth(object):

    AUTH_ERROR = 'auth_error'
    ACCESS_ERROR = 'access_error'
    GET_USERINFO_ERROR = 'get_userinfo_error'
    MSGS = {
        AUTH_ERROR: '授权失败',
        ACCESS_ERROR: '获取令牌失败',
        GET_USERINFO_ERROR: '获取用户信息失败',
    }

    SNSAPI_BASE = 'snsapi_base'
    SNSAPI_USERINFO = 'snsapi_userinfo'
    AUTH_URL = 'https://open.weixin.qq.com/connect/oauth2/authorize'
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
        self.client = werobot.client.Client(self.config.get('appid'),
            self.config.get('secret'))
        app.wxauth = self
        app.wxclient = self.client

        @app.route(self.config.get('wxauth_url', '/oauth/wechat/callback'))
        def wxauth_callback():
            return self.callback()

        app.jssdk = JSSDK(app)

    def quote(self, **kwargs):
        return dict((x, quote(y)) for x, y in kwargs.iteritems())

    def get_access_url(self, code):
        query = dict(
            appid=self.config.get('appid'),
            secret=self.config.get('secret'),
            code=code,
            grant_type='authorization_code',
        )
        return '%s?%s' % (self.ACCESS_URL, urlencode(query))

    @err_logger
    def access_token(self, code):
        url = self.get_access_url(code)
        return requests.get(url).json()

    def get_refresh_url(self, token):
        query = dict(
            appid=self.config.get('appid'),
            refresh_token=token,
            grant_type='refresh_token',
        )
        return '%s?%s' % (self.REFRESH_URL, urlencode(query))

    @err_logger
    def refresh_token(self, token):
        url = self.get_refresh_url(token)
        return requests.get(url).json()     

    def get_userinfo_url(self, token, openid, lang='zh_CN'):
        query = dict(access_token=token, openid=openid, lang=lang)
        return '%s?%s' % (self.USERINFO_URL, urlencode(query))

    @err_logger
    def get_userinfo(self, token, openid):
        url = self.get_userinfo_url(token, openid)
        return requests.get(url).json()

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

    def get_auth_url(self, next, scope=SNSAPI_BASE, state='STATE'):
        query = self.quote(
            appid=self.config.get('appid'),
            callback=url_for('wxauth_callback', scope=scope, next=next, _external=True),
            scope=scope,
            state=state,
        )
        return '{url}?appid={appid}&redirect_uri={callback}&response_type=code' \
            '&scope={scope}&state={state}#wechat_redirect'.format(url=self.AUTH_URL, **query)

    def auth(self, next, scope=SNSAPI_BASE, state='STATE'):
        return redirect(self.get_auth_url(next, scope, state))

    def callback(self):
        code = request.args.get('code')
        next = request.args.get('next')
        scope = request.args.get('scope', self.SNSAPI_BASE)

        if not code:
            return self.error(self.AUTH_ERROR, next)

        access = self.access_token(code)
        if not access or 'openid' not in access:
            log = 'access error\nnext: %s\ncode: %s\naccess: %s'
            current_app.logger.error(log % (next, code, str(access)))
            return self.error(self.ACCESS_ERROR, next)

        return self.success(access, next, scope)

    def success(self, access, next, scope):
        callback = self.success_callback
        if not callback:
            return '授权成功，请设置回调'

        res = callback(access, next, scope)
        return res if res else redirect(next)

    def error(self, err, next):
        res = '授权失败: %s' % err
        if self.error_callback:
            res = self.error_callback(err, next) or res
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

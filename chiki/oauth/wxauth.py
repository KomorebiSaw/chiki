# coding: utf-8
import json
import requests
import werobot.client
from chiki.api import abort, success
from chiki.api.const import *
from chiki.utils import err_logger, is_json, is_api
from chiki.oauth.jssdk import JSSDK
from datetime import datetime
from flask import current_app, request, redirect, url_for
from flask import make_response, render_template_string
from urllib import quote, urlencode

__all__ = [
    'WXAuth', 'init_wxauth',
]


class WXAuth(object):
    """微信登录有三种方式：公众号授权登录(mp)、扫码登录(qrcode)、手机登录(mobile)，
    只需相应加上配置，就支持相应的方式::

        WXAUTH = dict(
            mp=dict(
                appid='wx5d4a******b12c76',
                secret='bc1cdd******fd1496f1a8ae751f965b',
            ),
            mobile=dict(appid='', secret=''),
            qrcode=dict(appid='', secret=''),
        )
    """

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
    SNSAPI_LOGIN = 'snsapi_login'
    AUTH_CONNECT_URL = 'https://open.weixin.qq.com/connect/oauth2/authorize'
    AUTH_QRCONNECT_URL = 'https://open.weixin.qq.com/connect/qrconnect'
    ACCESS_URL = 'https://api.weixin.qq.com/sns/oauth2/access_token'
    REFRESH_URL = 'https://api.weixin.qq.com/sns/oauth2/refresh_token'
    USERINFO_URL = 'https://api.weixin.qq.com/sns/userinfo'
    CHECK_URL = 'https://api.weixin.qq.com/sns/auth'

    def __init__(self, app=None, config_key='WXAUTH'):
        self.config_key = config_key
        self.success_callback = None
        self.error_callback = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.config = app.config.get(self.config_key)
        self.endpoint = self.config.get('wxauth_endpoint', 'wxauth_callback')

        if not hasattr(app, 'wxauth'):
            app.wxauth = self

        mp = self.config.get(self.ACTION_MP)
        if mp:
            self.client = werobot.client.Client(
                mp.get('appid'), mp.get('secret'))
            if not hasattr(app, 'wxclient'):
                app.wxclient = self.client

        @app.route(
            self.config.get('wxauth_url', '/oauth/wechat/callback'),
            endpoint=self.endpoint)
        def wxauth_callback():
            return self.callback()

        @app.route(
            self.config.get('wxauth_js_url', '/weixin-login.js'),
            endpoint=self.config.get('wxauth_js_endpoint'))
        def weixin_login():
            qrcode = self.config.get(self.ACTION_QRCODE)
            js = ''
            if qrcode:
                config = dict(
                    id=request.args.get('id', ''),
                    appid=qrcode.get('appid', ''),
                    scope=self.SNSAPI_LOGIN,
                    redirect_uri=quote(url_for(
                        self.endpoint, scope=self.SNSAPI_LOGIN,
                        action=self.ACTION_QRCODE, _external=True)),
                    state='STATE',
                    style=request.args.get('style', 'white'),
                    href=request.args.get('href', ''),
                )
                js = render_template_string(
                    "var wxauth = new WxLogin({{ config | safe }});",
                    config=json.dumps(config))
            resp = make_response(js)
            resp.headers['Control-Cache'] = 'no-cache'
            resp.headers['Content-Type'] = 'text/javascript; charset=utf-8'
            return resp

        if self.config.get('allow_jssdk', True):
            app.jssdk = JSSDK(app)

    def quote(self, **kwargs):
        return dict((x, quote(y.encode('utf-8') if type(
            y) is unicode else y)) for x, y in kwargs.iteritems())

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
        try:
            return self.client.get_user_info(openid)
        except:
            self.client.refresh_token()
            return self.client.get_user_info(openid)

    def get_check_url(self, token, openid):
        query = dict(access_token=token, openid=openid)
        return '%s?%s' % (self.CHECK_URL, urlencode(query))

    @err_logger
    def check_token(self, token, openid):
        url = self.get_check_url(token, openid)
        return requests.get(url).json()['errcode'] == 0

    def get_auth_url(self, action, next, scope=SNSAPI_BASE, state='STATE'):
        if action == self.ACTION_QRCODE:
            scope = self.SNSAPI_LOGIN

        config = self.config.get(action)

        host = self.config.get('callback_host')
        if not host:
            callback = url_for(self.endpoint, scope=scope, next=next,
                               action=action, _external=True)
        else:
            callback = url_for(self.endpoint, scope=scope, next=next,
                               action=action)
            callback = 'http://%s%s' % (host, callback)
        query = self.quote(
            appid=config.get('appid'),
            callback=callback,
            scope=scope,
            state=state,
        )
        url = self.AUTH_CONNECT_URL
        if action != 'mp':
            url = self.AUTH_QRCONNECT_URL
        return '{url}?appid={appid}&redirect_uri={callback}' \
            '&response_type=code&scope={scope}&state={state}' \
            '#wechat_redirect'.format(url=url, **query)

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
        """发起微信登录，在需要的地方带用即可。

        :param action: 公众号授权登录(mp)、扫码登录(qrcode)
        :param next: 授权后下一步链接
        :param scope: snsapi_base|snsapi_userinfo
        :param state: STATE
        """
        action = self.get_action(action)
        if action == 'mobile' or is_json():
            return abort(WXAUTH_REQUIRED)

        return redirect(self.get_auth_url(action, next, scope, state))

    def callback(self):
        action = request.args.get('action', 'mp')
        code = request.args.get('code', '')
        next = request.args.get('next', '')
        scope = request.args.get('scope', self.SNSAPI_BASE)

        if request.host not in next and next.startswith('http://'):
            url = request.url.replace(
                request.host, urlparse.urlparse(next).netloc)
            return redirect(url)

        if action not in ['mp', 'mobile', 'qrcode']:
            return self.error(self.ARGS_ERROR, action, next)

        if not code:
            return self.error(self.AUTH_ERROR, action, next)

        access = self.access_token(action, code)
        if not access or 'openid' not in access:
            log = '%s\naccess error\naccess: %s\nurl: %s' \
                  '\nnext: %s\ncode: %s\naccess: %s'
            current_app.logger.error(log % (
                str(datetime.now()) + '-' * 80,
                self.get_access_url(action, code),
                request.url, next, code, str(access)))
            return self.error(self.ACCESS_ERROR, action, next)

        return self.success(action, scope, access, next)

    def success(self, action, scope, access, next):
        callback = self.success_callback
        if not callback:
            return '授权成功，请设置回调'

        res = callback(action, scope, access, next)
        if res:
            return res

        if is_json():
            if current_user.is_authenticated():
                return success()
            return error(msg='登录出错')
        return redirect(next)

    def error(self, err, action, next):
        if self.error_callback:
            res = self.error_callback(err, action, next)
            if res:
                return res
        if is_json():
            return error(msg='授权失败(%s): %s' % (action, err))
        return '授权失败(%s): %s' % (action, err)

    def success_handler(self, callback):
        """授权成功回调::

            @app.wxauth.success_handler
            def wxauth_success(action, scope, access, next):
                pass

        :param action: mp|qrcode|mobile
        :param scope: snsapi_base|snsapi_userinfo
        :param access: 微信授权成功返回的信息
        :param next: 下一步的链接
        :rtype: None或自定义Response
        """
        self.success_callback = callback
        return callback

    def error_handler(self, callback):
        """授权失败回调::

            @app.wxauth.error_handler
            def wxauth_error(err, action, next):
                pass

        :param err: 错误吗
        :param action: mp|qrcode|mobile
        :param next: 下一步的链接
        :rtype: None或自定义Response
        """
        self.error_callback = callback
        return callback


def init_wxauth(app):
    if app.config.get('WXAUTH'):
        return WXAuth(app)

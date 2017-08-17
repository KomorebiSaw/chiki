# coding: utf-8
import json
import traceback
import requests
import functools
from chiki.base import Base
from chiki.utils import sign, is_debug, add_args
from chiki.web import error
from chiki.api import success
from chiki.contrib.admin import AdminUser, AdminUserLoginLog, Group
from chiki.contrib.common import Item
from chiki.contrib.users import um
from flask import current_app, request, redirect, url_for
from flask.ext.login import current_user, login_user, encode_cookie
from urllib import urlencode

__all__ = [
    'IPay',
]


def enable_oauth(link_path):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated():
                return success(next=current_app.ipay.auth_url(link_path))

            if not is_debug() and not current_user.debug:
                res = current_app.ipay.access()
                if res.get('data', dict()).get('need_access'):
                    return success(next=current_app.ipay.auth_url(link_path))
            return func(*args, **kwargs)
        return wrapper
    return decorator


class IPay(Base):

    def __init__(self, app=None, key=None, config=None, holder=None):
        self.callback = None
        self.oauth_callback = None
        super(IPay, self).__init__(app, key, config, holder)

    def init_app(self, app):
        super(IPay, self).init_app(app)
        self.callback_host = app.config.get('CALLBACK_HOST')
        self.pid = self.get_config('pid')
        self.secret = self.get_config('secret')
        self.auto_auth = self.get_config('auto_auth', True)
        self.callback_url = self.get_config(
            'callback_url', '/callback/ipay/[key]/')
        self.endpoint = self.get_config(
            'endpoint', 'ipay_[key]_callback')
        self.oauth_callback_url = self.get_config(
            'oauth_callback_url', '/oauth/callback/ipay/[key]/')
        self.oauth_endpoint = self.get_config(
            'oauth_endpoint', 'ipay_[key]_dauth_callback')
        self.dash_oauth_callback_url = self.get_config(
            'dash_oauth_callback_url', '/oauth/callback/dash_ipay/[key]/')
        self.dash_oauth_endpoint = self.get_config(
            'dash_oauth_endpoint', 'ipay_[key]_dash_oauth_callback')

        @app.route(self.callback_url, endpoint=self.endpoint, methods=['POST'])
        def ipay_callback():
            res = ''
            try:
                data = dict(request.form.items())
                s = data.pop('sign', '')
                if s != sign(self.secret, **data):
                    return json.dumps(dict(code=1))

                if self.callback:
                    res = self.callback(self, data)
            except:
                current_app.logger.error(
                    'ipay callbck except: \n%s' % traceback.format_exc())
            return res or json.dumps(dict(code=0))

        @app.route(self.oauth_callback_url, endpoint=self.oauth_endpoint)
        def ipay_oauth_callback():
            xid = request.args.get('xid')
            xkey = request.args.get('xkey')
            next = request.args.get('next')

            if not current_user.is_authenticated():
                res = self.post('/access/key', xid=xid, xkey=xkey)
                if res.get('code') != 0:
                    if request.args.get('debug'):
                        return error(msg='授权失败：%s' % json.dumps(res))
                    return error(msg='授权失败')

                user = um.models.User.objects(xid=xid).first()
                if not user:
                    user = um.models.User(xid=xid)
                    user.create()

                    current_app.logger.info('ipay create user: %d %s' % (
                        user.id, user.xid))

                login_user(user, remember=True)

                if user.is_user() and not user.active:
                    return error(msg=Item.data(
                        'active_alert_text', '你的帐号已被封号处理！', name='封号提示'))

                if current_user.is_authenticated() and current_user.is_user():
                    um.models.UserLog.login(user.id, 'web', 'ipay')
                    user.login()

                um.funcs.on_wechat_login('ipay', next)

            host = Item.data('ipay_callback_host', '', name='测试重定向地址')
            if host:
                if next.startswith('http://'):
                    next = 'http://%s/%s' % (host, next[7:].split('/', 1)[1])
                elif next.startswith('/'):
                    next = 'http://%s%s' % (host, next)
            if request.args.get('token'):
                next = add_args(next, token=encode_cookie(unicode(current_user.id)))
            return redirect(next)

        @app.route(self.dash_oauth_callback_url,
                   endpoint=self.dash_oauth_endpoint)
        def ipay_dash_oauth_callback():
            xid = request.args.get('xid')
            xkey = request.args.get('xkey')
            next = request.args.get('next')

            res = self.post('/dash/access/key', xid=xid, xkey=xkey)
            if res.get('code') != 0:
                if request.args.get('debug'):
                    return error(msg='授权失败：%s' % json.dumps(res))
                return error(msg='授权失败')

            user = AdminUser.objects(xid=xid).first()
            if not user:
                user = AdminUser(xid=xid)

            res = res.get('data', dict())
            user.username = res.get('username')
            user.password = res.get('password')
            user.root = res.get('group') == 'root'
            user.group = Group.objects(name=res.get('group_name')).first()
            user.save()

            login_user(user)

            AdminUserLoginLog.login(user.id)
            return redirect(next)

    def handler(self, callback, recursion=True):
        self.callback = callback
        if recursion:
            for puppet in self.puppets.itervalues():
                puppet.handler(callback, recursion=recursion)
        return callback

    def oauth_handler(self, callback, recursion=True):
        self.oauth_callback = callback
        if recursion:
            for puppet in self.puppets.itervalues():
                puppet.oauth_handler(callback, recursion=recursion)
        return callback

    def prepay(self, **kwargs):
        kwargs.setdefault('name', '金币')
        kwargs.setdefault('price', 100)
        kwargs.setdefault('front_url', 'http://%s/' % request.host)
        host = self.callback_host if self.callback_host else request.host
        backurl = 'http://%s%s' % (host, url_for(self.endpoint))
        kwargs.setdefault('notify_url', backurl)
        return self.post('/payment/prepay', **kwargs)

    def transfer(self, **kwargs):
        kwargs.setdefault('name', '_')
        kwargs.setdefault('price', 100)
        host = self.callback_host if self.callback_host else request.host
        backurl = 'http://%s%s' % (host, url_for(self.endpoint))
        kwargs.setdefault('notify_url', backurl)
        return self.post('/payment/transfer', **kwargs)

    def access(self, **kwargs):
        if current_user.is_authenticated():
            kwargs.setdefault('oid', current_user.id)
            kwargs.setdefault('xid', current_user.xid)
        return self.post('/access', **kwargs)

    def post(self, url, **kwargs):
        if not url.startswith('http://'):
            host = Item.data('ipay_api_host', 'api.amroom.cn', name='iPay接口')
            url = 'http://%s%s' % (host, url)
        kwargs.setdefault('pid', self.pid)
        kwargs['sign'] = sign(self.secret, **kwargs)
        try:
            return requests.post(url, kwargs).json()
        except Exception, e:
            return dict(code=-1, key='ERROR', msg=str(e))

    def auth_url(self, next):
        host = Item.data(
            'ipay_auth_host', 'www.amroom.cn', name='iPay域名')
        next = url_for(self.oauth_endpoint, next=next, _external=True)
        query = urlencode(dict(pid=self.pid, next=next))
        return 'http://%s/oauth/access?%s' % (host, query)

    def dash_auth_url(self, next):
        host = Item.data(
            'ipay_dash_host', 'dash.amroom.cn', name='Dash域名')
        next = url_for(self.dash_oauth_endpoint, next=next, _external=True)
        query = urlencode(dict(pid=self.pid, next=next))
        return 'http://%s/oauth/access?%s' % (host, query)

    def auth(self, next):
        return redirect(self.auth_url(next))

    def dash_auth(self, next):
        return redirect(self.dash_auth_url(next))

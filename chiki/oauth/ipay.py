# coding: utf-8
import json
import traceback
import requests
from chiki.base import Base
from chiki.utils import sign
from chiki.web import error
from chiki.contrib.common import Item
from chiki.contrib.users import um
from flask import current_app, request, redirect, url_for
from flask.ext.login import current_user, login_user
from urllib import urlencode

__all__ = [
    'IPay',
]


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
            'oauth_endpoint', 'ipay_[key]_oauth_callback')

        @app.route(self.callback_url, endpoint=self.endpoint, methods=['POST'])
        def ipay_callback():
            res = ''
            try:
                data = request.form
                s = data.pop('sign', '')
                if s != sign(self.secret, **data.items()):
                    return json.dumps(code=1)
                if self.callback:
                    res = self.callback(self, data)
            except:
                current_app.logger.error(
                    'ipay callbck except: \n%s' % traceback.format_exc())
            return res or json.dumps(code=0)

        @app.route(self.oauth_callback_url, endpoint=self.oauth_endpoint)
        def ipay_oauth_callback():
            xid = request.args.get('xid')
            ukey = request.args.get('xkey')
            next = request.args.get('next')

            if current_user.is_authenticated():
                return redirect(next)

            res = self.post('/access/key', xid=xid, xkey=xkey)
            if res['code'] != 0:
                return error(msg='授权失败')

            user = um.models.User(xid=xid).first()
            if not user:
                user = um.models.User(xid=xid)
                user.create()

            login_user(user, remember=True)

            if user.is_user() and not user.active:
                return error(msg=Item.data(
                    'active_alert_text', '你的帐号已被封号处理！', name='封号提示'))

            if current_user.is_authenticated() and current_user.is_user():
                um.models.UserLog.login(user.id, 'web', 'ipay')
                user.login()

            um.funcs.on_wechat_login('ipay', next)
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

    def post(self, url, **kwargs):
        if not url.startswith('http://'):
            host = Item.data('ipay_api_host', 'api.example.com', name='iPay接口')
            url = 'http://%s%s' % (host, url)
        kwargs.setdefault('pid', self.pid)
        kwargs['sign'] = sign(self.secret, **kwargs.items())
        try:
            return requests.post(url, kwargs).json()
        except Exception, e:
            return dict(code=-1, key='ERROR', msg=str(e))

    def auth(self, next):
        host = Item.data(
            'ipay_auth_host', 'www.example.com', name='iPay域名')
        next = url_for(self.oauth_endpoint, next=next, _external=True)
        query = urlencode(dict(pid=self.pid, next=next))
        return redirect('http://%s/oauth/access?%s' % (host, query))
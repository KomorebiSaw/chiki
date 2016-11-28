# coding: utf-8
import rsa
import json
import base64
import traceback
from datetime import datetime
from flask import url_for, request, current_app
from urllib import quote

__all__ = [
    'Alipay', 'init_alipay',
]


class Alipay(object):

    def __init__(self, app=None, config_key='ALIPAY'):
        self.config_key = config_key
        self.callback = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.config = app.config.get(self.config_key)
        self.callback_url = self.config.get('callback_url', '/alipay/callback/')
        self.endpoint = self.config.get('endpoint', 'alipay_callback')
        self.app_id = self.config.get('app_id')
        try:
            self.app_private_key = rsa.PrivateKey.load_pkcs1(self.config.get('app_private_key'))
            self.alipay_public_key = rsa.PublicKey.load_pkcs1(self.config.get('alipay_public_key'))
        except ValueError:
            app.logger.error(traceback.format_exc())
            self.app_private_key = None
            self.alipay_public_key = None
        if not hasattr(app, 'alipay'):
            app.alipay = self

        @app.route(self.callback_url, methods=['POST'], endpoint=self.endpoint)
        def alipay_callback():
            self.alipay_callback()
            return "success"

    def alipay_callback(self):
        sign = request.args.get('sign')
        args = dict([(x, y) for x, y in request.args.iteritems() if x != 'sign'])
        if self.verify(sign, **args):
            if self.callback:
                self.callback()
        else:
            current_app.logger.error(
                'alipay callback not verify: %s' % json.dumps(request.args))

    def handler(self, callback):
        self.callback = callback
        return callback

    def notify_url(self, **kwargs):
        return url_for(self.endpoint, _external=True, **kwargs)

    def app_pay(self, **kwargs):
        kwargs.setdefault('timeout_express', '90m')
        kwargs.setdefault('product_code', 'QUICK_MSECURITY_PAY')
        res = dict(
            app_id=self.app_id,
            method='alipay.trade.app.pay',
            format='JSON',
            charset='utf-8',
            sign_type='RSA',
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            version='1.0',
            notify_url=current_app.alipay.notify_url(),
            biz_content=json.dumps(kwargs),
        )
        res['sign'] = self.sign(**res)
        return self.encode(res)

    def sign(self, **kwargs):
        keys = sorted(filter(lambda x: x[1], kwargs.iteritems()), key=lambda x: x[0])
        text = '&'.join(['%s=%s' % x for x in keys])
        return base64.b64encode(rsa.sign(text, self.app_private_key, 'SHA-1'))

    def verify(self, sign, **kwargs):
        keys = sorted(filter(lambda x: x[1], kwargs.iteritems()), key=lambda x: x[0])
        text = '&'.join(['%s=%s' % x for x in keys])
        try:
            rsa.verify(text, base64.b64decode(sign), self.alipay_public_key)
            return True
        except rsa.VerificationError:
            return False

    def encode(self, data):
        return '&'.join(['%s=%s' % (x[0], quote(x[1])) for x in data.iteritems()])


def init_alipay(app):
    if app.config.get('ALIPAY'):
        return Alipay(app)

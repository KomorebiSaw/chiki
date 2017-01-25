# coding: utf-8
import json
import base64
import hashlib
import requests
import traceback
from datetime import datetime, timedelta
from Crypto.Cipher import AES
from chiki.contrib.common import Item
from chiki.utils import randstr, today
from flask import request, current_app, url_for


class Near(object):

    HOST = 'pay.neargh.com'
    CALLBACK_HOST = ''
    PREPAY_URL = 'http://%s/paying/nongshanghang/getCodeUrl'
    QUERY_URL = 'http://%s/paying/nongshanghang/getPayStatus'

    def __init__(self, app=None, config_key='NEAR'):
        self.config_key = config_key
        self.callback = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        if not hasattr(app, 'near'):
            app.near = self
        self.config = app.config.get(self.config_key, {})
        self.host = self.config.get('host', self.HOST)
        self.callback_host = self.config.get(
            'callback_host', self.CALLBACK_HOST)
        self.callback_url = self.config.get(
            'callback_url', '/callback/near/')
        self.endpoint = self.config.get('endpoint', 'near_callback')

        @app.route(self.callback_url, endpoint=self.endpoint, methods=['POST'])
        def near_callback():
            pass

    def handler(self, callback):
        self.callback = callback
        return callback

    def prepay(self, **kwargs):
        kwargs.setdefault('body', '云计费')
        kwargs.setdefault('total_fee', 1)
        kwargs.setdefault('product_id', '20170101')
        kwargs.setdefault('goods_tag', 'default')
        kwargs.setdefault('op_user_id', self.config.get('op_user_id'))
        kwargs.setdefault('nonce_str', randstr(32))
        kwargs.setdefault('spbill_create_ip', self.config.get(
            'spbill_create_ip', '127.0.0.1'))
        kwargs['sign'] = self.sign(**kwargs)
        try:
            res = requests.post(
                self.PREPAY_URL % self.host, data=kwargs)
            current_app.logger.error('debug: ' + res.content)
            return res.json()
        except Exception, e:
            return dict(errcode=500, msg=str(e))

    def query(self, id):
        try:
            return requests.post(
                self.QUERY_URL % self.host, data=dict(tradeNum=id)).json()
        except Exception, e:
            return dict(errcode=500, msg=str(e))

    def sign(self, **kwargs):
        keys = sorted(
            filter(lambda x: x[1], kwargs.iteritems()), key=lambda x: x[0])
        text = '&'.join(['%s=%s' % x for x in keys])
        return hashlib.sha1(text.encode('utf-8')).hexdigest().upper()


def init_near(app):
    if 'NEAR' in app.config:
        return Near(app)

# coding: utf-8
import json
import base64
import hashlib
import requests
import traceback
from datetime import datetime, timedelta
from chiki.base import Base
from chiki.contrib.common import Item
from chiki.utils import randstr, today, get_ip
from flask import request, current_app, url_for


class Near(Base):

    HOST = 'test.neargh.com:8093'
    CALLBACK_HOST = ''
    PREPAY_URL = '/paying/lovepay/getQr'
    QUERY_URL = '/paying/lovepay/getPayState'

    def __init__(self, app=None, key=None, config=None, holder=None):
        self.callback = None
        super(Near, self).__init__(app, key, config, holder)

    def init_app(self, app):
        super(Near, self).init_app(app)

        self.host = self.get_config('host', self.HOST)
        self.prepay_url = self.get_config('prepay_url', self.PREPAY_URL)
        self.query_url = self.get_config('query_url', self.QUERY_URL)
        self.need_secret = self.get_config('need_secret', False)
        self.callback_host = self.get_config(
            'callback_host', self.CALLBACK_HOST)
        self.callback_url = self.get_config(
            'callback_url', '/callback/near/[key]/')
        self.endpoint = self.get_config(
            'endpoint', 'near_[key]_callback')

        @app.route(self.callback_url, endpoint=self.endpoint, methods=['POST'])
        def near_callback():
            res = ''
            try:
                res = json.loads(request.data)
                if self.callback:
                    res = self.callback(self, res)
            except:
                current_app.logger.error(
                    'near callbck except: \n%s' % traceback.format_exc())
            return res or json.dumps(dict(
                errcode=200,
                msg='成功接收请求',
                tradeNum=request.form.get('tradeNum', ''),
                notifyUrl=request.url,
            ))

    def handler(self, callback, recursion=True):
        self.callback = callback
        if recursion:
            for puppet in self.puppets.itervalues():
                puppet.handler(callback, recursion=recursion)
        return callback

    def prepay(self, **kwargs):
        kwargs.setdefault('body', '云计费')
        kwargs.setdefault('total_fee', '1')
        kwargs.setdefault('product_id', '20170101')
        kwargs.setdefault('goods_tag', 'default')
        kwargs.setdefault('op_user_id', self.get_config('key'))
        kwargs.setdefault('nonce_str', randstr(32))
        host = self.callback_host if self.callback_host else request.host
        backurl = 'http://%s%s' % (host, url_for(self.endpoint))
        kwargs.setdefault('notify_url', backurl)
        kwargs.setdefault('spbill_create_ip', self.get_config(
            'spbill_create_ip', get_ip()))
        kwargs['sign'] = self.sign(**kwargs)
        kwargs['total_fee'] = str(kwargs['total_fee'])

        url = 'http://%s%s' % (self.host, self.prepay_url)
        data = json.dumps(kwargs, ensure_ascii=False).encode('utf-8')
        if current_app.debug:
            print url
            print data

        try:
            return requests.post(url, data=data).json()
        except Exception, e:
            return dict(errcode=500, msg=str(e))

    def query(self, id):
        url = 'http://%s%s' % (self.host, self.prepay_url)
        try:
            data = json.dumps(dict(tradeNum=id))
            return requests.post(url, data=data).json()
        except Exception, e:
            return dict(errcode=500, msg=str(e))

    def sign(self, **kwargs):
        keys = sorted(
            filter(lambda x: x[1], kwargs.iteritems()), key=lambda x: x[0])
        text = '&'.join(['%s=%s' % x for x in keys])
        if self.need_secret:
            text += self.get_config('secret')
        if current_app.debug:
            print text
        return hashlib.sha1(text.encode('utf-8')).hexdigest().upper()

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


class FaFa(Base):

    HOST = 'api.88.la'
    CALLBACK_HOST = ''
    PREPAY_URL = 'http://%s/PayApi/Index'

    def __init__(self, app=None, key=None, config=None, holder=None):
        self.callback = None
        super(FaFa, self).__init__(app, key, config, holder)

    def init_app(self, app):
        super(FaFa, self).init_app(app)

        self.host = self.get_config('host', self.HOST)
        self.callback_host = self.get_config(
            'callback_host', self.CALLBACK_HOST)
        self.callback_url = self.get_config(
            'callback_url', '/callback/fafa/[key]/')
        self.endpoint = self.get_config(
            'endpoint', 'fafa_[key]_callback')

        @app.route(self.callback_url, endpoint=self.endpoint, methods=['POST'])
        def fafa_callback():
            res = ''
            try:
                data = json.loads(request.data)
                sign = data.pop('Sign', None)
                if sign != self.sign_callback(**data):
                    tpl = 'res sign callbck: \n' \
                          'sign: %s\ncurr_sign: %s\ndata:\n%s'
                    current_app.logger.error(
                        tpl % (sign, self.sign_callback(**data), request.data))
                    return 'sign error'
                if self.callback:
                    res = self.callback(self, data)
            except:
                current_app.logger.error(
                    'fafa callbck except: \n%s' % traceback.format_exc())
            return res or 'success'

    def handler(self, callback, recursion=True):
        self.callback = callback
        if recursion:
            for puppet in self.puppets.itervalues():
                puppet.handler(callback, recursion=recursion)
        return callback

    def prepay(self, **kwargs):
        kwargs.setdefault('MchId', self.config.get('mchid'))
        kwargs.setdefault('PayTypeId', 'wechat_wap')
        kwargs.setdefault('TradeContent', '云计费')
        kwargs.setdefault('TradeAttach', '云计费')
        kwargs.setdefault('TradeMoney', 1)
        kwargs.setdefault('Ip', get_ip())

        host = self.callback_host if self.callback_host else request.host
        backurl = 'http://%s%s' % (host, url_for(self.endpoint))
        kwargs.setdefault('NotifyUrl', backurl)
        kwargs.setdefault('RedirectUrl', 'http://%s/' % request.host)
        kwargs['Sign'] = self.sign(**kwargs)
        try:
            return requests.post(
                self.PREPAY_URL % self.host, data=json.dumps(kwargs),
                timeout=8).json()
        except Exception, e:
            return dict(Error=-1, Message=str(e))

    def sign(self, **kwargs):
        keys = ['MchId', 'PayTypeId', 'MchTradeNo', 'TradeContent',
                'TradeAttach', 'TradeMoney', 'Ip', 'NotifyUrl']
        text = ''.join([str(kwargs.get(x, '')) for x in keys])
        text += self.get_config('key')
        return hashlib.md5(text.encode('utf-8')).hexdigest().lower()

    def sign_callback(self, **kwargs):
        keys = ['Error', 'Message', 'MchId', 'MchTradeNo',
                'OutTradeNo', 'TradeAttach', 'ActuallyMoney', 'TimeEnd']
        text = ''.join([str(kwargs.get(x, '')) for x in keys])
        text += self.get_config('key')
        return hashlib.md5(text.encode('utf-8')).hexdigest().lower()

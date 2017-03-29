# coding: utf-8
import hashlib
import requests
import traceback
from chiki.base import Base
from chiki.utils import get_ip, randstr
from flask import request, url_for, current_app
from werobot.utils import to_text
from xml.etree import ElementTree
from dicttoxml import dicttoxml


class Swift(Base):

    HOST = 'pay.swiftpass.cn'
    CALLBACK_HOST = ''
    PREPAY_URL = 'https://%s/pay/gateway'

    def __init__(self, app=None, key=None, config=None, holder=None):
        self.callback = None
        super(Swift, self).__init__(app, key, config, holder)

    def init_app(self, app):
        super(Swift, self).init_app(app)

        self.host = self.get_config('host', self.HOST)
        self.callback_host = self.get_config(
            'callback_host', self.CALLBACK_HOST)
        self.callback_url = self.get_config(
            'callback_url', '/callback/swift/[key]/')
        self.endpoint = self.get_config(
            'endpoint', 'swift_[key]_callback')

        @app.route(self.callback_url, endpoint=self.endpoint, methods=['POST'])
        def swift_callback():
            res = ''
            try:
                data = self.xml2dict(request.data)
                sign = data.pop('sign', None)
                if sign != self.sign(**data):
                    tpl = 'swift sign callbck: \nsign: %s\ncurr_sign: %s\ndata:\n%s'
                    current_app.logger.error(
                        tpl % (sign, self.sign(**data), request.data))
                    return 'sign error'
                if self.callback:
                    res = self.callback(self, data)
            except Exception, e:
                current_app.logger.error('wxpay callbck except: %s' % str(e))
            return res or 'success'

    def handler(self, callback, recursion=True):
        self.callback = callback
        if recursion:
            for puppet in self.puppets.itervalues():
                puppet.handler(callback, recursion=recursion)
        return callback

    def xml2dict(self, xml):
        doc = ElementTree.fromstring(xml)
        return dict((x.tag, to_text(x.text)) for x in doc)

    def prepay(self, **kwargs):
        kwargs.setdefault('service', 'pay.weixin.jspay')
        kwargs.setdefault('mch_id', self.get_config('mchid'))
        kwargs.setdefault('body', '云计费')
        kwargs.setdefault('total_fee', 1)
        kwargs.setdefault('mch_create_ip', self.get_config('mch_create_ip', '127.0.0.1'))
        host = self.callback_host if self.callback_host else request.host
        backurl = 'http://%s%s' % (host, url_for(self.endpoint))
        kwargs.setdefault('notify_url', backurl)
        kwargs.setdefault('callback_url', 'http://%s/' % request.host)
        kwargs.setdefault('nonce_str', randstr(32))
        kwargs['sign'] = self.sign(**kwargs)

        data = dicttoxml(kwargs, custom_root='xml', attr_type=False)
        try:
            xml = requests.post(self.PREPAY_URL % self.host, data=data).content
            return self.xml2dict(xml)
        except Exception, e:
            current_app.logger.error(traceback.format_exc())
            return dict(status=-1, message=str(e))

    def sign(self, **kwargs):
        keys = sorted(
            filter(lambda x: x[1], kwargs.iteritems()), key=lambda x: x[0])
        text = '&'.join(['%s=%s' % x for x in keys])
        text += '&key=%s' % self.get_config('key')
        return hashlib.md5(text.encode('utf-8')).hexdigest().upper()

    def pay_url(self, id):
        return 'https://%s/pay/jspay?token_id=%s' % (self.host, id)

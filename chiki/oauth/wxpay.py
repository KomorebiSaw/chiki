# coding: utf-8
import json
import time
import hashlib
import requests
from chiki.utils import get_ip, randstr
from flask import request, url_for, current_app
from werobot.utils import to_text
from xml.etree import ElementTree
from dicttoxml import dicttoxml

__all__ = [
    'WXPay', 'init_wxpay',
]


class WXPay(object):

    PREPAY_URL = 'https://api.mch.weixin.qq.com/pay/unifiedorder'
    SEND_RED_PACK = 'https://api.mch.weixin.qq.com/mmpaymkttransfers/sendredpack'

    def __init__(self, app=None):
        self.wxpay_callback = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.config = app.config.get('WXPAY')
        app.wxpay = self

        @app.route('/wxpay/callback', methods=['POST'])
        def wxpay_callback():
            self.callback()
            return """
<xml>
  <return_code><![CDATA[SUCCESS]]></return_code>
  <return_msg><![CDATA[OK]]></return_msg>
</xml>
"""

    def callback(self):
        res = ''
        try:
            data = self.xml2dict(request.data)
            sign = data.pop('sign', None)
            if sign != self.sign(**data):
                current_app.logger.error('wxpay callbck: %s' % request.data)
                return 'sign error'
            if self.wxpay_callback:
                res = self.wxpay_callback(data)
        except Exception, e:
            current_app.logger.error('wxpay callbck except: %s' % str(e))
        return res or ''

    def wxpay_handler(self, callback):
        self.wxpay_callback = callback
        return callback

    def xml2dict(self, xml):
        doc = ElementTree.fromstring(xml)
        return dict((x.tag, to_text(x.text)) for x in doc)

    def prepay(self, **kwargs):
        kwargs.setdefault('appid', self.config.get('appid'))
        kwargs.setdefault('mch_id', self.config.get('mchid'))
        kwargs.setdefault('spbill_create_ip', get_ip())
        kwargs.setdefault('notify_url', url_for('wxpay_callback', _external=True))
        kwargs.setdefault('trade_type', 'JSAPI')
        kwargs.setdefault('body', '微信支付')
        kwargs.setdefault('out_trade_no', 'wxtest')
        kwargs.setdefault('total_fee', 100)
        kwargs.setdefault('nonce_str', randstr(32))
        kwargs.setdefault('sign', self.sign(**kwargs))

        if 'openid' not in kwargs:
            raise ValueError('openid is required.')

        data = dicttoxml(kwargs, custom_root='xml', attr_type=False)
        try:
            xml = requests.post(self.PREPAY_URL, data=data).content
            return self.xml2dict(xml)
        except Exception, e:
            return dict(return_code='ERROR', return_msg=str(e))

    def send_red_pack(self, **kwargs):
        kwargs.setdefault('wxappid', self.config.get('appid'))
        kwargs.setdefault('mch_id', self.config.get('mchid'))
        kwargs.setdefault('client_ip', self.config.get('client_ip'))
        kwargs.setdefault('send_name', self.config.get('send_name', '小酷科技'))
        kwargs.setdefault('total_amount', 100)
        kwargs.setdefault('total_num', 1)
        kwargs.setdefault('nonce_str', randstr(32))
        kwargs.setdefault('wishing', '恭喜发财')
        kwargs.setdefault('act_name', '现金红包')
        kwargs.setdefault('remark', '备注')
        kwargs['mch_billno'] = kwargs['mch_id'] + kwargs.get('mch_billno', '')
        kwargs.setdefault('sign', self.sign(**kwargs))

        if 're_openid' not in kwargs:
            raise ValueError('re_openid is required.')

        data = dicttoxml(kwargs, custom_root='xml', attr_type=False)
        try:
            xml = requests.post(self.SEND_RED_PACK, data=data, cert=self.config.get('cert')).content
            return self.xml2dict(xml)
        except Exception, e:
            return dict(return_code='ERROR', return_msg=str(e))

    def sign(self, **kwargs):
        text = '&'.join(['%s=%s' % x for x in sorted(kwargs.iteritems(), key=lambda x: x[0])])
        text += '&key=%s' % self.config.get('key')
        return hashlib.md5(text.encode('utf-8')).hexdigest().upper()

    def get_conf(self, prepay, tojson=True):
        conf = dict(
            appId=self.config.get('appid'),
            timeStamp=str(int(time.time())),
            nonceStr=randstr(32),
            package='prepay_id=%s' % prepay,
            signType='MD5',
        )
        conf['paySign'] = self.sign(**conf)
        return json.dumps(conf) if tojson else conf


def init_wxpay(app):
    if app.config.get('WXPAY'):
        return WXPay(app)

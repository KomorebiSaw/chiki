# coding: utf-8
import json
import time
import hashlib
import requests
import inspect
from chiki.utils import get_ip, randstr
from flask import request, url_for, current_app
from werobot.utils import to_text
from xml.etree import ElementTree
from dicttoxml import dicttoxml

__all__ = [
    'WXPay', 'init_wxpay',
]


class WXPay(object):
    """微信支付目前只封装了公众号支付的相关功能：支付、发红包、退款、查询退款。
    微信支付的配置(WXPAY)，加上即启用::

        WXPAY = dict(
            appid='wx5d4a******b12c76',              # APPID
            mchid='13******01',                      # 商户号
            key='206ef4acf8c2******b43480712cc762',  # 支付key，对应在商户平台设置
            send_name='月光宝石',                     # 发红包的名字(发红包才需要)
            client_ip='127.0.0.1',                   # 服务器的公网IP(发红包才需要)
            cert=(                                   # 发红包、退款用到的密钥
                os.path.join(ETC_FOLDER, 'cert/apiclient_cert.pem'),
                os.path.join(ETC_FOLDER, 'cert/apiclient_key.pem'),
            )
        )
    """

    PREPAY_URL = 'https://api.mch.weixin.qq.com/pay/unifiedorder'
    REFUND_URL = 'https://api.mch.weixin.qq.com/secapi/pay/refund'
    REFUND_QUERY = 'https://api.mch.weixin.qq.com/pay/refundquery'
    SEND_RED_PACK = 'https://api.mch.weixin.qq.com/mmpaymkttransfers/sendredpack'

    def __init__(self, app=None, config_key='WXPAY',
            callback_url='/wxpay/<type>/callback/'):
        self.config_key = config_key
        self.callback_url = callback_url
        self.wxpay_callback = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.config = app.config.get('WXPAY')
        self.endpoint = self.config.get('endpoint', 'wxpay_callback')
        if not hasattr(app, 'wxpay'):
            app.wxpay = self

        @app.route(self.callback_url, methods=['POST'],
                endpoint=self.endpoint)
        def wxpay_callback(type='normal'):
            self.callback(type)
            return """
<xml>
  <return_code><![CDATA[SUCCESS]]></return_code>
  <return_msg><![CDATA[OK]]></return_msg>
</xml>
"""

    def callback(self, type='normal'):
        res = ''
        try:
            data = self.xml2dict(request.data)
            sign = data.pop('sign', None)
            if sign != self.sign(**data):
                tpl = 'wxpay sign callbck: \nsign: %s\ncurr_sign: %s\ndata:\n%s'
                current_app.logger.error(tpl % (sign, self.sign(**data), request.data))
                return 'sign error'
            if self.wxpay_callback:
                if len(inspect.getargspec(self.wxpay_callback)[0]) == 1:
                    res = self.wxpay_callback(data)
                else:
                    res = self.wxpay_callback(data, type)
        except Exception, e:
            current_app.logger.error('wxpay callbck except: %s' % str(e))
        return res or ''

    def wxpay_handler(self, callback):
        """支付结果回调::

            @wxpay.wxpay_handler
            def wxpay_handler(res, type):
                pass

        :param res: 回调的信息
        :param type: 预支付传过来的类型
        """
        self.wxpay_callback = callback
        return callback

    def xml2dict(self, xml):
        doc = ElementTree.fromstring(xml)
        return dict((x.tag, to_text(x.text)) for x in doc)

    def prepay(self, **kwargs):
        """微信支付预付款下单，对接口进行封装。

        :param body: 订单名称
        :param detail: 订单详情
        :param out_trade_no: 订单号
        :param openid: 用户OpenID
        :param type: 订单分类，默认为normal
        :rtype: 微信接口返回结果
        """
        type = kwargs.pop('type', 'normal')
        kwargs.setdefault('appid', self.config.get('appid'))
        kwargs.setdefault('mch_id', self.config.get('mchid'))
        kwargs.setdefault('spbill_create_ip', get_ip())
        kwargs.setdefault('notify_url', url_for(self.endpoint, type=type, _external=True))
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
        """微信支付发红包，对接口进行封装。

        :param total_amount: 金额总数
        :param total_num: 红包数量
        :param wishing: 祝福语
        :param act_name: 活动名称
        :param remark: 备注
        :param re_openid: 用户OpenID
        :rtype: 微信接口返回结果
        """
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

    def refund(self, **kwargs):
        """微信支付申请退款，对接口进行封装。

        :param out_trade_no: 订单号
        :param out_refund_no: 退款记录ID
        :param total_fee: 订单金额
        :param refund_fee: 退款金额
        :rtype: 微信接口返回结果
        """
        if 'out_trade_no' not in kwargs:
            raise ValueError('out_trade_no is required.')

        kwargs.setdefault('appid', self.config.get('appid'))
        kwargs.setdefault('mch_id', self.config.get('mchid'))
        kwargs.setdefault('device_info', 'WEB')
        kwargs.setdefault('out_refund_no', kwargs.get('out_trade_no'))
        kwargs.setdefault('total_fee', 1)
        kwargs.setdefault('refund_fee', kwargs.get('total_fee'))
        kwargs.setdefault('refund_fee_type', 'CNY')
        kwargs.setdefault('op_user_id', self.config.get('mchid'))
        kwargs.setdefault('nonce_str', randstr(32))
        kwargs.setdefault('sign', self.sign(**kwargs))

        data = dicttoxml(kwargs, custom_root='xml', attr_type=False)
        try:
            xml = requests.post(self.REFUND_URL, data=data, cert=self.config.get('cert')).content
            return self.xml2dict(xml)
        except Exception, e:
            return dict(return_code='ERROR', return_msg=str(e))

    def refund_query(self, **kwargs):
        """微信支付退款查询，对接口进行封装。

        :param out_trade_no: 订单号
        :rtype: 微信接口返回结果
        """
        kwargs.setdefault('appid', self.config.get('appid'))
        kwargs.setdefault('mch_id', self.config.get('mchid'))
        kwargs.setdefault('device_info', 'WEB')
        kwargs.setdefault('nonce_str', randstr(32))
        kwargs.setdefault('sign', self.sign(**kwargs))

        data = dicttoxml(kwargs, custom_root='xml', attr_type=False)
        try:
            xml = requests.post(self.REFUND_QUERY, data=data).content
            return self.xml2dict(xml)
        except Exception, e:
            return dict(return_code='ERROR', return_msg=str(e))

    def sign(self, **kwargs):
        keys = sorted(filter(lambda x: x[1], kwargs.iteritems()), key=lambda x: x[0])
        text = '&'.join(['%s=%s' % x for x in keys])
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

# coding: utf-8
import hashlib
import requests
import traceback
from chiki.utils import randstr
from flask import request, current_app, url_for


class YeDaDou(object):

    HOST = 'pay.yedadou.com'
    PREPAY_URL = 'http://%s/unifiOrder' % HOST

    def __init__(self, app=None, config_key='YEDADOU'):
        self.config_key = config_key
        self.callback = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.yedadou = self
        self.config = app.config.get(self.config_key, {})

        @app.route('/callback/yedadou/', methods=['POST'])
        def yedadou_callback():
            res = ''
            try:
                data = dict((x, y[0]) for x, y in request.form.iteritems())
                sign = data.pop('sign', None)
                if sign != self.sign(**data):
                    tpl = 'yedadou sign callbck: \n' \
                          'sign: %s\ncurr_sign: %s\ndata:\n%s'
                    current_app.logger.error(
                        tpl % (sign, self.sign(**data), request.data))
                    return 'sign error'
                if self.callback:
                    res = self.callback(data)
            except:
                current_app.logger.error(
                    'yedadou callbck except: \n%s' % traceback.format_exc())
            return res or 'success'

    def handler(self, callback):
        self.callback = callback
        return callback

    def prepay(self, **kwargs):
        kwargs.setdefault('title', '云计费')
        kwargs.setdefault('mch_id', self.config.get('mchid'))
        kwargs.setdefault('amount_fee', 1)
        kwargs.setdefault('sign_type', 'MD5')
        kwargs.setdefault('notify_url', url_for(
            'yedadou_callback', _external=True))
        kwargs.setdefault('return_url', 'http://%s/' % request.host)
        kwargs.setdefault('nonce_str', randstr(32))
        kwargs['sign'] = self.sign(**kwargs)
        try:
            return requests.post(self.PREPAY_URL, data=kwargs).json()
        except Exception, e:
            return dict(result_code=-1, return_msg=str(e))

    def sign(self, **kwargs):
        keys = sorted(
            filter(lambda x: x[1], kwargs.iteritems()), key=lambda x: x[0])
        text = '&'.join(['%s=%s' % x for x in keys])
        text += '&key=%s' % self.config.get('key')
        return hashlib.md5(text.encode('utf-8')).hexdigest().upper()


def init_yedadou(app):
    if 'YEDADOU' in app.config:
        return YeDaDou(app)

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


def base64_url_decode(inp):
    inp = inp.replace('-', '+')
    inp = inp.replace('_', '/')
    inp = inp.replace('.', '=')
    return base64.b64decode(inp)


def base64_url_encode(inp):
    code = base64.b64encode(inp)
    code = code.replace('+', '-')
    code = code.replace('/', '_')
    return code.replace('=', '.')


class SiWei(object):

    HOST = 'zfapi.cnkwl.cn'
    CALLBACK_HOST = ''
    URL = 'http://%s/openapi/%s'

    def __init__(self, app=None, config_key='SIWEI'):
        self.config_key = config_key
        self.callback = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        if not hasattr(app, 'siwei'):
            app.siwei = self
        self.config = app.config.get(self.config_key, {})
        self.host = self.config.get('host', self.HOST)
        self.callback_host = self.config.get(
            'callback_host', self.CALLBACK_HOST)
        self.callback_url = self.config.get(
            'callback_url', '/callback/siwei/')
        self.endpoint = self.config.get('endpoint', 'siwei_callback')

        @app.route(self.callback_url, endpoint=self.endpoint, methods=['POST'])
        def siwei_callback():
            res = ''
            try:
                data = request.form.get('Data', request.form.get('data', ''))
                sign = request.form.get('Sign', request.form.get('sign', ''))
                secretkey = self.config.get('secretkey')
                text = data + secretkey
                curr_sign = hashlib.md5(text).hexdigest().lower()
                if sign != curr_sign:
                    tpl = 'siwei sign callbck: \n' \
                          'sign: %s\ncurr_sign: %s\ndata:\n%s'
                    current_app.logger.error(
                        tpl % (sign, curr_sign, request.form))
                    return '{"message":"签名错误","response":"-1"}'
                if self.callback:
                    res = self.callback(self.decode(data, self.config.get('aes_key')))
            except:
                current_app.logger.error(
                    'siwei callbck except: \n%s' % traceback.format_exc())
            return res or '{"message":"成功","response":"00"}'

    def handler(self, callback):
        self.callback = callback
        return callback

    @property
    def token(self):
        now = datetime.now()
        key = self.config.get('config_key', 'siwei:token')
        token = json.loads(Item.data(key, '{}'))
        if not token or datetime.strptime(
                token['deadline'], '%Y-%m-%d %H:%M:%S') <= now:
            token = self.grant_token()
            if token:
                if not token['persisted']:
                    token['deadline'] = today() + timedelta(seconds=1800)
                else:
                    token['deadline'] = now + timedelta(seconds=token['persisted'])
                token['deadline'] = token['deadline'].strftime('%Y-%m-%d %H:%M:%S')
                Item.set_data(key, json.dumps(token))
        return token

    def grant_token(self):
        url = self.URL % (self.host, 'oauth/getToken.do')
        data = dict(
            loginname=self.config.get('loginname'),
            loginpwd=self.config.get('loginpwd'),
        )
        res = self.get(url, session=False, **data)
        if res['ret'] != 0:
            current_app.logger.error(
                'siwei grant_token error: \n%s' % json.dumps(res))
            return dict()
        return res['data']

    def padding(self, text, bs=16):
        return text + (bs - len(text) % bs) * chr(0)

    def encode(self, data, key):
        aes = AES.new(key, AES.MODE_CBC, key)
        data = self.padding(json.dumps(data))
        return base64_url_encode(aes.encrypt(data))

    def decode(self, data, key):
        aes = AES.new(key, AES.MODE_CBC, key)
        return json.loads(aes.decrypt(base64_url_decode(data)).rstrip('\0'))

    def get(self, url, session=True, html=False, **kwargs):
        data = dict(
            appid=self.config.get('appid'),
            format='json',
            v='2.0',
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        )
        if session:
            token = self.token
            secretkey = token.get('secretkey')
            data['data'] = self.encode(kwargs, secretkey)
            data['session'] = token.get('session', '')
            text = (secretkey + data['appid'] + data['data'] +
                    data['format'] + data['session'] + data['timestamp'] +
                    data['v'] + secretkey)
            data['sign'] = hashlib.md5(text).hexdigest().lower()
        else:
            secretkey = self.config.get('secretkey')
            data['data'] = self.encode(kwargs, secretkey)
            text = (secretkey + data['appid'] + data['data'] +
                    data['format'] + data['timestamp'] +
                    data['v'] + secretkey)
            data['sign'] = hashlib.md5(text).hexdigest().lower()
        try:
            if html:
                return requests.get(url, params=data)
            return requests.get(url, params=data).json()
        except Exception, e:
            return dict(ret=-1, message=str(e))

    def prepay(self, **kwargs):
        kwargs.setdefault('subcompanyid', self.config.get('subcompanyid'))
        kwargs.setdefault('body', '云计费')
        kwargs.setdefault('amount', 1)
        kwargs.setdefault('businesstype', 1001)
        kwargs.setdefault('paymenttypeid', 10000)
        kwargs.setdefault('fronturl', 'http://%s/' % request.host)

        host = self.callback_host if self.callback_host else request.host
        backurl = 'http://%s%s' % (host, url_for(self.endpoint))
        kwargs.setdefault('backurl', backurl)
        return self.get(self.URL % (self.host, 'pay/pay.do'), **kwargs)


def init_siwei(app):
    if 'SIWEI' in app.config:
        return SiWei(app)

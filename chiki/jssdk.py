# coding: utf-8
import time
import json
import random
import requests
import hashlib
import string
from flask import current_app, request, render_template_string
from flask import make_response
from chiki.contrib.common import Item

DEFAULT_JS_API_LIST = [x.strip() for x in """
onMenuShareTimeline|onMenuShareAppMessage|onMenuShareQQ|
onMenuShareWeibo|onMenuShareQZone|startRecord|stopRecord|
onVoiceRecordEnd|playVoice|pauseVoice|stopVoice|onVoicePlayEnd|
uploadVoice|downloadVoice|chooseImage|previewImage|uploadImage|
downloadImage|translateVoice|getNetworkType|openLocation|
getLocation|hideOptionMenu|showOptionMenu|hideMenuItems|
showMenuItems|hideAllNonBaseMenuItem|showAllNonBaseMenuItem|
closeWindow|scanQRCode|chooseWXPay|openProductSpecificView|
addCard|chooseCard|openCard""".split('|')]


class JSSDK(object):

    TPL = 'https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token=%s&type=jsapi'

    def __init__(self, app=None):
        self._ticket = ''
        self._expires_at = 0
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        app.jssdk = self

        @app.route('/weixin-config.js')
        def weixin_config():
            apis = Item.data('wx_js_api_list').split('|')
            if not apis or not apis[0]:
                apis = DEFAULT_JS_API_LIST
            apis = [str(x) for x in apis]
            sign = self.sign
            config = dict(
                debug=str(request.args.get('debug', 'false')),
                appId=current_app.config.get('WXAUTH', {}).get('appid'),
                timestamp=sign['timestamp'],
                nonceStr=sign['nonceStr'],
                signature=sign['signature'],
                jsApiList=apis,
            )
            js = render_template_string("wx.config({{ config | safe }});",
                config=json.dumps(config))
            resp = make_response(js)
            resp.headers['Control-Cache'] = 'no-cache'
            resp.headers['Content-Type'] = 'text/javascript; charset=utf-8'
            return resp

    @property
    def nonce(self):
        a = lambda: random.choice(string.ascii_letters + string.digits)
        return ''.join(a() for _ in range(15))

    @property
    def ticket(self):
        now = int(time.time())
        if self._expires_at - now < 60:
            self.refresh()

        return self._ticket

    def refresh(self):
        url = self.TPL % current_app.wxclient.token
        res = requests.get(url).json()
        if res['errcode'] != 0:
            current_app.logger.error(str(res))
            return ''
        
        self._ticket = res['ticket']
        self._expires_at = res['expires_in'] + time.time()
        return self._ticket

    @property
    def sign(self):
        res = dict(
            nonceStr=self.nonce,
            timestamp=int(time.time()),
            jsapi_ticket=self.ticket,
            url=request.args.get('url', request.headers.get('Referer', request.url)),
        )
        text = '&'.join(['%s=%s' % (x.lower(), res[x]) for x in sorted(res)])
        res['signature'] = hashlib.sha1(text).hexdigest()
        res['text'] = text
        Item.set_data('jssdk:info', json.dumps(res))
        return res

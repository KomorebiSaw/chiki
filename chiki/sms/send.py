# coding: utf-8 
import re
import urllib
import socket
import ConfigParser
from flask import current_app
from .CCPRestSDK import REST

__all__ = [
    'send_rong_sms', 'send_ihuyi_sms',
]


def send_rong_sms(phone, datas, temp_id):
    settings = current_app.config.get('SMS_RONG')
    host = settings.get('host', 'app.cloopen.com')
    port = settings.get('port', 8883)
    version = settings.get('version', '2013-12-26')
    sid = settings.get('sid')
    token = settings.get('token')
    appid = settings.get('appid')

    rest = REST(host, str(port), version)
    rest.setAccount(sid, token)
    rest.setAppId(appid)
    result = rest.sendTemplateSMS(phone, datas, temp_id)
    
    return result.get("statusCode") == "000000"


def send_ihuyi_sms(phone, text):
    settings = current_app.config.get('SMS_IHUYI')
    params = dict(
        account=settings['account'],
        password=settings['password'],
        mobile=phone,
        content=text,
    )
    tpl = 'http://106.ihuyi.cn/webservice/sms.php?method=Submit&%s'
    url = tpl % urllib.urlencode(params)

    for i in range(3):
        try:
            res = urllib.urlopen(url).read()
            break
        except (IOError, socket.error):
            pass
    
    return True if re.search(r'<code>2</code>', res) else False
        
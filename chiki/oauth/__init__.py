# coding: utf-8
from .alipay import *
from .wxauth import *
from .wxpay import *
from .jssdk import *
from .robot import *
from .wxmsg import *


def init_oauth(app):
    init_alipay(app)
    init_wxauth(app)
    init_wxpay(app)
    init_wxmsg(app)

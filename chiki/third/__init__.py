# coding: utf-8
from .express import *
from .yedadou import *
from .siwei import *
from .swift import *
from .fafa import *
from .near import *


def init_third(app):
    init_express(app)
    init_yedadou(app)
    init_siwei(app)
    init_swift(app)
    init_fafa(app)
    init_near(app)

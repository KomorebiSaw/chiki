# coding: utf-8
from .express import *
from .yedadou import *
from .siwei import *


def init_third(app):
    init_express(app)
    init_yedadou(app)
    init_siwei(app)

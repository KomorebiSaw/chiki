# coding: utf-8
from .wxauth import *
from .jssdk import *
from .robot import *


def init_oauth(app):
    init_wxauth(app)

# coding: utf-8
from .express import *
from .yedadou import *
from .siwei import *
from .swift import *
from .fafa import *
from .near import *
from .ngh import *


def init_third(app):
    init_express(app)
    init_yedadou(app)
    init_siwei(app)
    FaFa.init(app)
    NGH.init(app)
    Near.init(app)
    Swift.init(app)

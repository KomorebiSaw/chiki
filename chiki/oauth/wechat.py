# coding: utf-8


class WeChat(object):

    def __init__(self, app=None):
        if app:
            self.init_app(app)
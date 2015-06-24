# coding: utf-8
import os
from flask import send_from_directory

__all__ = [
    'Uploads', 'init_uploads',
]


class Uploads(object):

    def __init__(self, app=None, config='UPLOADS'):
        self.config = config
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        conf = app.config.get(self.config)
        @app.route(conf['link'] % '<path:filename>')
        def uploads(filename):
            return send_from_directory(conf['path'], filename)


def init_uploads(app, config='UPLOADS'):
    Uploads(app, config)
# coding: utf-8
from flask.ext.admin import Admin as _Admin
from .formatters import *
from .views import *


class Admin(_Admin):

    def __init__(self, app=None, name=None,
                 url=None, subdomain=None,
                 index_view=None,
                 translations_path=None,
                 endpoint=None,
                 static_url_path=None,
                 base_template=None,
                 template_mode='chiki',
                 category_icon_classes=None):
        super(Admin, self).__init__(app=app, name=name,
            url=url, subdomain=subdomain,
            index_view=index_view,
            translations_path=translations_path,
            endpoint=endpoint,
            static_url_path=static_url_path,
            base_template=base_template,
            template_mode=template_mode,
            category_icon_classes=category_icon_classes,
        )

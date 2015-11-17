# coding: utf-8
from chiki import AttrDict
from chiki.base import db
from . import admin, apis, forms, models, views
from .base import user_manager

__all__ = [
    'user_manager', 'UserManager',
]


class UserManager(object):

    def __init__(self, app=None):
        self.models = AttrDict()
        self.forms = AttrDict()
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        app.user_manager = self
        self.init_models()
        self.init_forms()

    def init_models(self):
        for key in models.__all__:
            if key not in self.models:
                self.models[key] = getattr(models, key)

    def init_forms(self):
        for key in forms.__all__:
            if key not in self.forms:
                self.forms[key] = getattr(forms, key)

    def add_model(self, model):
        self.models[model.__name__] = model
        return model

    def add_form(self, form):
        self.forms[form.__name__] = form
        return form

    def init_admin(self, admin):
        pass

    def init_apis(self, api, wapi=None):
        pass

    def init_views(self, app):
        pass

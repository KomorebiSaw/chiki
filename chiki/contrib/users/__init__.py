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
        self.apis = AttrDict()
        self.models = AttrDict()
        self.forms = AttrDict()
        self.funcs = AttrDict()
        self.config = AttrDict()
        self.init_models()
        self.init_forms()
        self.init_funcs()
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        app.user_manager = self
        self.init_config()
        self.init_resources()

    def init_config(self):
        config = self.app.config.get('CHIKI_USER', {})
        self.config.allow_email = config.get('allow_email', False)
        self.config.allow_phone = config.get('allow_phone', True)
        self.config.register_auto_login = config.get('register_auto_login', True)
        self.config.reset_password_auto_login = config.get('reset_password_auto_login', True)
        self.config.include_apis = config.get('include_apis', {})
        self.config.exclude_apis = config.get('exclude_apis', {})

    def init_models(self):
        for key in models.__all__:
            if key not in self.models:
                self.models[key] = getattr(models, key)

    def init_forms(self):
        for key in forms.__all__:
            if key not in self.forms:
                self.forms[key] = getattr(forms, key)

    def init_funcs(self):
        for key in apis.__all__:
            if key not in self.funcs:
                func = getattr(apis, key)
                if callable(func):
                    self.funcs[key] = func

    def init_resources(self):
        for key in apis.resources:
            if key not in self.apis \
                    and key not in self.config.exclude_apis \
                    and (not self.config.include_apis or key in self.config.include_apis):
                self.apis[key] = apis.resources.get(key)

    def add_model(self, model):
        self.models[model.__name__] = model
        return model

    def add_form(self, form):
        self.forms[form.__name__] = form
        return form

    def add_func(self, func):
        self.funcs[func.__name__] = func
        return func

    def add_api(self, *args, **kwargs):
        def wrapper(cls):
            self.apis[key] = (cls, args, kwargs)
        return wrapper

    def init_apis(self, api):
        for cls, args, kwargs in self.apis.itervalues():
            _web = kwargs.pop('_web', False)
            api.add_resource(cls, *args, **kwargs)
            kwargs['_web'] = _web

    def init_wapis(self, api):
        for cls, args, kwargs in self.apis.itervalues():
            _web = kwargs.pop('_web', False)
            api.add_resource(cls, *args, **kwargs)
            kwargs['_web'] = _web

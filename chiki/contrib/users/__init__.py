# coding: utf-8
from chiki import AttrDict, init_verify
from chiki.base import db
from chiki.contrib.users import admin, apis, forms, funcs, models, oauth, views
from chiki.contrib.users.base import user_manager
from flask.ext.login import LoginManager

__all__ = [
    'user_manager', 'um', 'UserManager',
]

um = user_manager


class UserManager(object):

    def __init__(self, app=None):
        self.apis = AttrDict()
        self.models = AttrDict()
        self.forms = AttrDict()
        self.funcs = AttrDict()
        self.config = AttrDict()
        self.tpls = AttrDict()
        self.init_models()
        self.init_forms()
        self.init_funcs()
        self.init_tpls()
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        app.user_manager = self
        self.init_login()
        self.init_config()
        self.init_resources()
        self.init_oauth()
        self.init_jinja()
        init_verify(app)

    def init_login(self):
        self.login = LoginManager(self.app)
        self.login.login_view = 'users.login'

        @self.login.user_loader
        def load_user(id):
            if type(id) == str:
                if id.startswith('wechat:'):
                    return um.models.WeChatUser.objects(id=id.split(':')[-1]).first()
                elif id.startswith('qq:'):
                    return um.models.QQUser.objects(id=id.split(':')[-1]).first()
                elif id.startswith('weibo:'):
                    return um.models.WeiBoUser.objects(id=id.split(':')[-1]).first()
            return um.models.User.objects(id=id).first()

    def init_config(self):
        config = self.app.config.get('CHIKI_USER', {})
        self.allow_email = self.config.allow_email = config.get('allow_email', False)
        self.allow_phone = self.config.allow_phone = config.get('allow_phone', True)
        self.config.register_auto_login = config.get('register_auto_login', True)
        self.config.reset_password_auto_login = config.get('reset_password_auto_login', True)
        self.config.include_apis = config.get('include_apis', {})
        self.config.exclude_apis = config.get('exclude_apis', {})
        self.config.allow_oauth_urls = config.get('allow_oauth_urls',
            ['users.logout', 'users.bind', 'bindphone', 'bindemail', 'bindauto',
                'sendemailcode', 'authemailcode', 'sendphonecode', 'authphonecode',
                'static', 'verify_code', 'uploads'])
        self.config.oauth_model = config.get('oauth_model', 'select')
        self.config.oauth_remember = config.get('oauth_remeber', True)
        self.config.bind_url = config.get('bind_url', '/users/bind.html')
        self.config.login_next = config.get('login_next', '/')

    def init_models(self):
        for key in models.__all__:
            if key not in self.models:
                self.models[key] = getattr(models, key)

    def init_forms(self):
        for key in forms.__all__:
            if key not in self.forms:
                self.forms[key] = getattr(forms, key)

    def init_funcs(self):
        for module in [apis, funcs, oauth]:
            for key in module.__all__:
                if key not in self.funcs:
                    func = getattr(module, key)
                    if callable(func):
                        self.funcs[key] = func

    def init_tpls(self):
        self.tpls.login = 'users/login.html'
        self.tpls.register = 'users/register.html'
        self.tpls.register_email = 'users/register_email.html'
        self.tpls.reset_password = 'users/reset_password.html'
        self.tpls.reset_password_email = 'users/reset_password_email.html'
        self.tpls.bind = 'users/bind.html'

    def init_resources(self):
        for key in apis.resources:
            if key not in self.apis \
                    and key not in self.config.exclude_apis \
                    and (not self.config.include_apis or key in self.config.include_apis):
                self.apis[key] = apis.resources.get(key)

    def init_oauth(self):
        self.funcs.init_oauth(self.app)

    def init_jinja(self):
        self.app.context_processor(self.context_processor)

    def context_processor(self):
        return dict(um=self)

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
            _api = kwargs.pop('_api', True)
            if _api == True:
                api.add_resource(cls, *args, **kwargs)
            kwargs['_web'] = _web
            kwargs['_api'] = _api

    def init_wapis(self, api):
        for cls, args, kwargs in self.apis.itervalues():
            _web = kwargs.pop('_web', False)
            _api = kwargs.pop('_api', True)
            if _web == True:
                api.add_resource(cls, *args, **kwargs)
            kwargs['_web'] = _web
            kwargs['_api'] = _api

    def init_web(self):
        self.app.register_blueprint(views.bp, url_prefix='/users')

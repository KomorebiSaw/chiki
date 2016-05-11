# coding: utf-8
from chiki import is_json
from chiki.api.const import *
from flask import current_app, request, redirect
from flask.ext.login import current_user, login_user
from . import wechat
from .wechat import *

__all__ = [
    'init_oauth',
] + wechat.__all__


def init_oauth(app):
    init_wxauth(app)

    @app.before_request
    def before_request():
        if current_user.is_authenticated() \
                and request.endpoint not in current_app.user_manager.config.allow_oauth_urls \
                and not request.path.startswith('/admin'):

            um = current_app.user_manager
            model = um.config.oauth_model
            remember = um.config.oauth_remember
            if not current_user.is_user():
                if model == 'auto':
                    user = um.models.User.from_oauth(current_user)
                    login_user(user, remember=remember)
                    return
            elif current_user.phone or current_user.email or model == 'auto':
                return

            if is_json():
                abort(NEED_BIND)
            return redirect(current_app.user_manager.config.bind_url)

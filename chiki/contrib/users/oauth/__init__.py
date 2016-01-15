# coding: utf-8
from chiki import is_json
from chiki.api.const import *
from flask import current_app, request, redirect
from flask.ext.login import current_user
from . import wechat
from .wechat import *

__all__ = [
    'init_oauth',
] + wechat.__all__


def init_oauth(app):
    init_wxauth(app)

    @app.before_request
    def before_request():
        if current_user.is_authenticated() and not current_user.is_user() \
                and request.endpoint not in current_app.user_manager.config.allow_oauth_urls \
                and not request.path.startswith('/admin'):

            model = current_app.user_manager.config.oauth_model
            remember = current_app.user_manager.config.oauth_remember
            current_app.logger.error(model)
            if model == 'auto':
                user = um.models.User.from_oauth(current_user)
                login_user(user, remember=remember)
                return
            if is_json():
                abort(NEED_BIND)
            return redirect(current_app.user_manager.config.bind_url)

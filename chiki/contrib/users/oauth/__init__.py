# coding: utf-8
from chiki import is_json
from chiki.web import error
from chiki.api.const import *
from chiki.contrib.common import Item
from flask import current_app, request, redirect
from flask.ext.login import current_user, login_user, logout_user
from urllib import urlencode
from . import wechat
from .wechat import *

__all__ = [
    'init_oauth',
] + wechat.__all__


def init_oauth(app):
    init_wxauth(app)

    @app.before_request
    def before_request():
        if current_user.is_authenticated() and current_user.is_user() and not current_user.active:
            logout_user()
            error(msg=Item.data('active_alert_text', '你的帐号已被封号处理！', name='封号提示'))

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

            query = urlencode(dict(next=request.url))
            return redirect('%s?%s' % (current_app.user_manager.config.bind_url, query))

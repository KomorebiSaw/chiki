# coding: utf-8
from chiki.web import error
from chiki.api.const import *
from chiki.contrib.common import Item
from chiki.utils import is_json
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
        if current_app.is_admin:
            return

        if current_user.is_authenticated():
            if 'channel' in str(current_user.get_id()):
                return

            if current_user.is_user() and not current_user.active:
                logout_user()
                return error(msg=Item.data(
                    'active_alert_text', '你的帐号已被封号处理！', name='封号提示'))

            config = current_app.user_manager.config
            if request.endpoint not in config.allow_oauth_urls:
                um = current_app.user_manager
                model = um.config.oauth_model
                remember = um.config.oauth_remember

                um.models.User.heart()
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
            return redirect('%s?%s' % (config.bind_url, query))

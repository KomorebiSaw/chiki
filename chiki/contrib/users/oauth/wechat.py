# coding: utf-8
import traceback
from chiki.api import abort
from chiki.api.const import *
from chiki.contrib.common import Item, Channel
from chiki.web import error
from chiki.utils import get_url_arg, is_json
from flask import current_app
from flask.ext.login import login_user, current_user

__all__ = [
    'init_wxauth', 'get_wechat_user', 'create_wechat_user',
    'wechat_login', 'on_wechat_login', 'on_invite',
]


def get_wechat_user(access, action='mp'):
    um = current_app.user_manager
    openid = '%s_openid' % action
    if 'unionid' in access and access['unionid']:
        wxuser = um.models.WeChatUser.objects(
            unionid=access['unionid']).first()
    else:
        query = {openid: access['openid']}
        wxuser = um.models.WeChatUser.objects(**query).first()
    if wxuser and not getattr(wxuser, openid):
        setattr(wxuser, openid, access['openid'])
        wxuser.save()
    return wxuser


def create_wechat_user(userinfo, action):
    um = current_app.user_manager
    return um.models.WeChatUser.create(userinfo, action)


def wechat_login(wxuser):
    um = current_app.user_manager
    model = um.config.oauth_model
    if model == 'auto' and not wxuser.current:
        um.models.User.from_wechat(wxuser)
    wxuser.update()


def on_invite(user, uid):
    um = current_app.user_manager
    if not user.inviter and uid and uid != user.id:
        inviter = um.models.User.objects(id=uid).first()
        if inviter and inviter.active and inviter.is_allow_invite(user):
            ids = []
            ids.append(inviter.inviter.id if inviter.inviter else 0)
            ids.append(inviter.inviter2.id if inviter.inviter2 else 0)
            ids.append(inviter.inviter3.id if inviter.inviter3 else 0)
            if user.id not in ids:
                if inviter.is_allow_channel(user):
                    user.channel = inviter.channel
                else:
                    user.channel = 1000
                inviter.on_invite(user)
                user.inviter = inviter
                user.inviter2 = inviter.inviter
                user.inviter3 = inviter.inviter2
                user.save()

                subs = list(um.models.User.objects(inviter=user.id).all())
                for x in subs:
                    x.inviter2 = user.inviter
                    x.inviter3 = user.inviter2
                    x.save()

                subs2 = list(um.models.User.objects(inviter__in=subs).all())
                for x in subs2:
                    x.inviter2 = user
                    x.inviter3 = user.inviter
                    x.save()

        if not inviter and uid < 100000:
            if not user.channel:
                channel = Channel.objects(id=uid).first()
                if channel:
                    user.channel = channel.id
                    user.inviter = um.models.User(id=100000)
                    user.save()
            else:
                user.channel = 1000
                user.inviter = um.models.User(id=100000)
                user.save()


def on_wechat_login(action, next):
    um = current_app.user_manager
    if current_user.is_authenticated() and \
            current_user.is_user() and \
            not current_user.inviter:
        try:
            uid = int(get_url_arg(next, 'uid') or 0)
            um.funcs.on_invite(current_user, uid)
        except:
            current_app.logger.error(traceback.format_exc())


def init_wxauth(app):
    if not hasattr(app, 'wxauth'):
        return

    wxauth = app.wxauth
    um = app.user_manager

    @wxauth.success_handler
    def wxauth_success(action, scope, access, next):
        user = um.funcs.get_wechat_user(access, action)
        if not user:
            if wxauth.SNSAPI_USERINFO not in access['scope'] \
                    and wxauth.SNSAPI_LOGIN not in access['scope']:
                return wxauth.auth(action, next, wxauth.SNSAPI_USERINFO)

            userinfo = wxauth.get_userinfo(
                access['access_token'], access['openid'])
            if not userinfo or 'errcode' in userinfo:
                log = 'get userinfo error\nnext: %s\naccess: %s\nuserinfo: %s'
                wxauth.app.logger.error(
                    log % (next, str(access), str(userinfo)))
                return wxauth.error(wxauth.GET_USERINFO_ERROR, action, next)

            user = um.funcs.create_wechat_user(userinfo, action)

        um.funcs.wechat_login(user)

        if user.user:
            real_user = um.models.User.objects(id=user.user).first()
            if not real_user:
                user.user = 0
                user.save()
            else:
                user = real_user

        login_user(user, remember=True)

        if user.is_user() and not user.active:
            return error(msg=Item.data(
                'active_alert_text', '你的帐号已被封号处理！', name='封号提示'))

        if current_user.is_authenticated() and current_user.is_user():
            um.models.UserLog.login(user.id, 'web', 'wechat')
            user.login()

        return um.funcs.on_wechat_login(action, next)

    @wxauth.error_handler
    def wxauth_error(err, action, next):
        if is_json():
            abort(WXAUTH_ERROR, wxcode=err, wxmsg=wxauth.MSGS.get(err, '未知错误'))

        return error('微信授权失败')

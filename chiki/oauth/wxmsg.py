# coding: utf-8
from .robot import WeRoBot
from .admin import *
from .models import *

__all__ = [
    'WXMsg', 'init_wxmsg',
]

robot = WeRoBot()


class WXMsg(object):

    def __init__(self, app=None):
        self.subscribe_callback = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.init_robot(robot)
        robot.init_app(app)
        robot.logger = app.logger

    def init_robot(self, robot):
        @robot.text
        def on_text(message):
            msg = Message.objects(keyword=message.content).first()
            if msg:
                reply = msg.reply(message)
                if reply:
                    return reply

            default_msg = Message.objects(default=True).first()
            if default_msg:
                return default_msg.reply(message)
            return ''

        @robot.subscribe
        @robot.scan
        def on_subscribe(message):
            if self.subscribe_callback:
                res = self.subscribe_callback(message)
                if res:
                    return res
            follow_msg = Message.objects(follow=True).first()
            if follow_msg:
                return follow_msg.reply(message)
            default_msg = Message.objects(default=True).first()
            if default_msg:
                return default_msg.reply(message)
            return ''

        @robot.unsubscribe
        def on_unsubscribe(message):
            user = um.models.User.get_wechat(mp_openid=message.source)
            if user:
                user.wechat_user.unsubscribe()

    def subscribe_handler(self, callback):
        self.subscribe_callback = callback
        return callback


def init_wxmsg(app):
    if app.config.get('WEROBOT_TOKEN') and app.config.get('WXMSG', True):
        return WXMsg(app)

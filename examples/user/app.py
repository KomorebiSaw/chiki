# coding: utf-8
from chiki import init_web
from chiki.contrib.users import UserManager


class Config(object):
    pass


def init(app):
    user = UserManager(app)


app = init_web(init, Config)


if __name__ == '__main__':
    app.run(debug=True)

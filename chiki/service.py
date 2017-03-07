# coding: utf-8
import inspect

cmds = dict()


def service(cmd=None, model='simple'):
    def add(func):
        c = cmd or func.__name__
        if cmd not in cmds:
            cmds[c] = dict()
        cmds[c][model] = func
        return func
    return add


def run(cmd, model='simple'):
    if cmd in cmds:
        func = cmds[cmd].get(model, cmds[cmd].get('simple'))
        if func:
            if inspect.getargspec(func)[0]:
                func(model)
            else:
                func()
            return True
    return False

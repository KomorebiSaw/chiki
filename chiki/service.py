# coding: utf-8
import os
import fcntl
import inspect
from functools import wraps

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


def single(filename):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            pid = str(os.getpid())
            pidfile = open(filename, 'a+')
            try:
                # 创建一个排他锁,并且所被锁住其他进程不会阻塞
                fcntl.flock(pidfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                return

            pidfile.seek(0)
            pidfile.truncate()
            pidfile.write(pid)
            pidfile.flush()
            pidfile.seek(0)

            res = func(*args, **kwargs)

            try:
                pidfile.close()
            except IOError, err:
                if err.errno != 9:
                    return
            os.remove(filename)
            return res
        return wrapper
    return decorator

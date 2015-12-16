# coding: utf-8


def condom(key):
    def desc(func):
        def wrapper(*args, **kwarg):
            return func(*args, **kwarg)
        return wrapper
    return desc

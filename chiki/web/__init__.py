#　coding: utf-8
from flask import request


def message(msg, style='info'):
    return msg


def success(msg):
    return message(msg, style='success')


def error(msg):
    return message(msg, style='danger')


def is_ajax():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest' \
        or request.args.get('ajax') == 'true'

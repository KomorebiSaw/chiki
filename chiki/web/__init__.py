#　coding: utf-8
from flask import request, render_template


def message(msg, style='info', url=''):
    return render_template('msg.html', msg=msg, style=style, url=url)


def success(msg, url=''):
    return message(msg, style='success', url=url)


def error(msg, url=''):
    return message(msg, style='danger', url=url)


def is_ajax():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest' \
        or request.args.get('ajax') == 'true'

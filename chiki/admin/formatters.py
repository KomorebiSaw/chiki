# coding: utf-8
from xml.sax.saxutils import escape as _escape, quoteattr
from ..iptools import parse_ip
from ..jinja import markup, markupper
from ..utils import datetime2best, time2best


def quote(*args):
    return tuple(quoteattr(x) for x in args)


def escape(*args):
    return tuple(_escape(x) for x in args)


def get_span(text, short):
    if text.startswith('http://'):
        return '<a href=%s title=%s target="_blank">%s</a>' % (
            quote(text, text) + escape(short))
    return '<span title=%s>%s</span>' % (quote(text) + escape(short))


def popover(content, short=None, title=None, placement='right'):
    short = title if short is None else short
    return '<a href="javascript:;" data-container="body" data-toggle="popover" ' \
            'data-trigger="focus" data-placement=%s title=%s data-content=%s data-html="true">%s</a>' % (
            quote(placement, title or '', content) + escape(short))


def formatter(func):
    def wrapper(view, context, model, name):
        if hasattr(model.__class__, name):
            data = unicode(getattr(model, name) or '')
            return markup(func(data) or '')
        return ''
    return wrapper


def formatter_model(func):
    def wrapper(view, context, model, name):
        return markup(func(model))
    return wrapper


def formatter_len(max_len=20):
    @formatter
    def wrapper(data):
        if len(data) > max_len + 1:
            return get_span(data, data[:max_len] + '...')
        return data
    return wrapper


def formatter_text(func, max_len=20):
    @formatter_model
    def span(model):
        short, text = func(model)
        short = short[:max_len] + '...' if len(short) > max_len + 1 else short
        return get_span(text, short)
    return span


def formatter_popover(func, max_len=20, show_title=True):
    @formatter_model
    def span(model):
        res = func(model)
        if len(res) == 3:
            short, title, content = res
        elif len(res) == 2:
            title, content = res
            short = title
        short = short[:max_len] + '...' if len(short) > max_len + 1 else short
        return popover(content, title=title if show_title else None, short=short)
    return span


def formatter_icon(func=None, height=40):

    tpl = u'''
        <a href=%%s target="_blank">
            <img src=%%s style="max-height: %dpx; margin: -6px">
        </a>
    ''' % height

    def icon(url):
        if url:
            if type(url) == list:
                return ''.join([icon(u) for u in url])
            if type(url) == tuple:
                if url[0] and url[1]:
                    return tpl % quote(url[1], url[0])
            else:
                return tpl % quote(url, url)
        return ''

    @formatter_model
    def wrapper(model):
        url = func(model) if func is not None else url
        return icon(url)
        
    return wrapper


def formatter_ip(url=None):
    @formatter
    def wrapper(ip):
        if ip:
            text = parse_ip(ip)
            if url:
                href = url(ip) if callable(url) else url % dict(ip=ip)
                return '<a href=%s title=%s target="_blank">%s</a>' % (
                    quote(href, ip) + escape(text))
            return '<span title=%s>%s</span>' % (quote(ip) + escape(text))
    return wrapper


@formatter
def format_time(t):
    return str(t).split('.')[0]


@formatter
def format_date(t):
    return str(t).split(' ')[0]


@formatter
def format_best(t):
    return get_span(str(t).split('.')[0], datetime2best(t))


def format_choices(view, context, model, name):
    if hasattr(model.__class__, name):
        field = getattr(model.__class__, name)
        data = getattr(model, name)
        choices = field.choices
        if choices:
            return dict(choices).get(data, data)

@markupper
def type_best(view, t):
    return get_span(str(t).split('.')[0], datetime2best(t))
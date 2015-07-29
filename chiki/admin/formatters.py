# coding: utf-8
from xml.sax.saxutils import escape as _escape, quoteattr
from ..iptools import parse_ip
from ..jinja import markup, markupper
from ..utils import datetime2best, time2best


def quote(*args):
    return tuple(quoteattr(unicode(x)) for x in args)


def escape(*args):
    return tuple(_escape(unicode(x)) for x in args)


def get_span(text, short):
    if text.startswith('http://'):
        return '<a href=%s title=%s target="_blank">%s</a>' % (
            quote(text, text) + escape(short))
    return '<span title=%s>%s</span>' % (quote(text) + escape(short))


def get_link(text, link, max_len=20, blank=True):
    tpl = u'<a href=%s title=%s target="_blank">%s</a>'
    if not blank:
        tpl = u'<a href=%s title=%s>%s</a>'
    if text or type(text) == int:
        short = unicode(text)[:max_len] + '...' if unicode(str(text)) > max_len else str(text)
        return tpl % (quote(link, text) + escape(short))
    return ''


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
        return markup(func(model) or '')
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
        short, text = unicode(short), unicode(text)
        short = short[:max_len] + '...' if len(short) > max_len + 1 else short
        return get_span(text, short)
    return span


def formatter_popover(func, max_len=20, show_title=True):
    @formatter_model
    def span(model):
        res = func(model)
        if not res:
            return
        if isinstance(res, (tuple, list)):
            if len(res) == 3:
                short, title, content = res
            elif len(res) == 2:
                title, content = res
                short = title
        else:
            short, title, content = res, None, res
        short = short[:max_len] + '...' if len(short) > max_len + 1 else short
        return popover(content, title=title if show_title else None, short=short)
    return span


def formatter_icon(func=None, height=40, **kwargs):
    if 'class_' in kwargs:
        kwargs['class'] = kwargs.pop('class_')
    exts = ' '.join(['%s=%s' % ((k,) + quote(v)) for k, v in kwargs.iteritems()]) + ' '
    tpl = u'''
        <a href=%%s target="_blank" style="text-decoration:none">
            <img %ssrc=%%s style="max-height: %dpx; margin: -6px 0">
        </a>
    ''' % (exts, height)


    def icon(url):
        if url:
            if isinstance(url, list):
                return ''.join([icon(u) for u in url])
            if isinstance(url, tuple):
                if url[0] and url[1]:
                    return tpl % quote(url[1], url[0])
            else:
                return tpl % quote(url, url)
        return ''

    @formatter_model
    def wrapper(model):
        return icon(func(model))
        
    return wrapper


def formatter_link(func, max_len=20, blank=True):

    @formatter_model
    def wrapper(model):
        res = func(model)
        if isinstance(res, list):
            return ','.join([get_link(x[0], x[1], max_len, blank) for x in res])
        return get_link(res[0], res[1], max_len, blank)

    return wrapper


def formatter_ip(url=None, blank=True):
    tpl = '<a href=%s title=%s target="_blank">%s</a>'
    if not blank:
        tpl = '<a href=%s title=%s>%s</a>'
    @formatter
    def wrapper(ip):
        if ip:
            text = parse_ip(ip)
            if url:
                href = url(ip) if callable(url) else url % dict(ip=ip)
                return tpl % (quote(href, ip) + escape(text))
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


@markupper
def type_image(view, image):
    tpl = u'''
        <a href=%s target="_blank" style="text-decoration:none">
            <img src=%s style="max-height: 40px; margin: -6px 0">
        </a>
    '''
    if image and image.link:
        return tpl % quote(image.link, image.get_link(50, 40))
    return ''
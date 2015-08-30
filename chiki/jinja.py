# coding: utf-8
from flask import current_app, get_flashed_messages
from jinja2 import Markup
from xml.sax.saxutils import escape
from .utils import time2best as _time2best

__all__ = [
    'markup', 'markupper', 'first_error', 'text2html',
    'JinjaManager', 'init_jinja',
]


def markup(html):
    return Markup(html) if current_app.jinja_env.autoescape else html


def markupper(func):
    def wrapper(*args, **kwargs):
        return markup(func(*args, **kwargs))
    return wrapper

    
def first_error(form):
    for field in form:
        if field.errors:
            return field.errors[0]


def text2html(text):
    out = ['']
    for line in text.splitlines():
        if not line.strip():
            out.append('')
            continue
        out[-1] += escape(line) + '<br>'
    return ''.join(u'<p>%s</p>' % x for x in filter(lambda x: x.strip, out))


class JinjaManager(object):

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.jinja_env.filters.update(self.filters)
        app.context_processor(self.context_processor)

    @property
    def filters(self):
        return dict(
            time2best=self.time2best,
            time2date=self.time2date,
            line2br=self.line2br_filter,
            text2html=self.text2html_filter,
            kform=self.kform_filter,
            kfiled=self.kfield_filter,
            kform_inline=self.kform_inline_filter,
            kfield_inline=self.kfield_inline_filter,
            alert=self.alert_filter,
            rmb=self.rmb_filter,
        )

    def context_processor(self):
        return dict(
            alert=self.alert_filter,
        )

    def line2br_filter(self, text):
        return markup(escape(text).replace('\n', '<br>'))

    def text2html_filter(self, text):
        return markup(text2html(text))

    def kform_filter(self, form, label=3):
        label_class = 'control-label col-sm-%d' % label
        field_div = '<div class="col-sm-%d">' % (12 - label)
        out = []
        for field in form:
            if field.type not in['CSRFTokenField', 'HiddenField']:
                out.append('<div class="form-group">')
                out.append(field.label(class_=label_class))
                out.append(field_div)
                if field.type == 'KRadioField':
                    out.append(field(sub_class='radio-inline'))
                elif field.type == 'KCheckboxField':
                    out.append(field(sub_class='checkbox-inline'))
                else:
                    if hasattr(field, 'addon'):
                        out.append('<div class="input-group">')
                        out.append(field(class_='form-control', data_label=field.label.text))
                        out.append('<span class="input-group-addon">%s</span>' % field.addon)
                        out.append('</div>')
                    else:
                        out.append(field(class_='form-control', data_label=field.label.text))
                out.append('</div></div>')
            else:
                out.append(field())
        return markup(''.join(out))

    def kfield_filter(self, field, **kwargs):
        out = []
        if field.type in ['CSRFTokenField', 'HiddenField']:
            out.append(field(**kwargs))
        else:
            kwargs.setdefault('class_', 'form-control')
            kwargs.setdefault('data_label', field.label.text)
            out.append('<div class="form-group">')
            out.append(field.label(class_='control-label'))
            if hasattr(field, 'addon'):
                out.append('<div class="input-group">')
                out.append(field(**kwargs))
                out.append('<span class="input-group-addon">%s</span>' % field.addon)
                out.append('</div>')
            else:
                out.append(field(**kwargs))
            out.append('</div>')
        return markup(''.join(out)) 

    def kform_inline_filter(self, form):
        out = []
        for field in form:
            out.append(self.kfield_inline_filter(field))
        return markup(''.join(out))

    def kfield_inline_filter(self, field, **kwargs):
        out = []
        if field.type in ['CSRFTokenField', 'HiddenField']:
            out.append(field(**kwargs))
        else:
            out.append('<div class="form-group">')
            if field.type == 'BooleanField':
                out.append('<div class="checkbox"><label>%s %s</label></div>' 
                    % (field(**kwargs), field.label.text))
            else:
                kwargs.setdefault('class_', 'form-control')
                kwargs.setdefault('data_label', field.label.text)
                kwargs.setdefault('placeholder', field.label.text)
                out.append(field(**kwargs))
            out.append('</div>')
        return markup(''.join(out))

    def alert_msg(self, msg, style='danger'):
        return markup('<div class="alert alert-%s"><button class="close" '
            'type="button" data-dismiss="alert" aria-hidden="true">&times;'
            '</button><span>%s</span></div>' % (style, msg))

    def alert_filter(self, form=None, style='danger'):
        error = first_error(form)
        if error:
            return self.alert_msg(error, style)

        messages = get_flashed_messages(with_categories=True)
        if messages:
            return self.alert_msg(messages[-1][1], messages[-1][0] or 'danger')
        return ''

    def rmb_filter(self, money):
        return '%.2f' % money

    def time2best(self, input):
        return _time2best(input)

    def time2date(self, input):
        return str(input)[:10]


def init_jinja(app):
    jinja = JinjaManager()
    jinja.init_app(app)

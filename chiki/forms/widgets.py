# coding: utf-8
from flask import url_for
from wtforms.widgets import html_params, HTMLString, TextArea
from wtforms.compat import text_type
from cgi import escape

__all__ = [
    'VerifyCode', 'UEditor', 'KListWidget', 'FileInput',
    'ImageInput', 'AreaInput', 'WangEditor',
]


class VerifyCode(object):

    html_params = staticmethod(html_params)

    def __call__(self, field, **kwargs):
        if field.hidden == True:
            html = '<input %s>' % self.html_params(
                id=field.id,
                type='hidden',
                name=field.name,
                value=field._value(),
            )
        else:
            html = '<div class="input-group">'
            html += '<input %s>' % self.html_params(
                id=field.id,
                type='text',
                name=field.name,
                value=field._value(),
                maxlength=field.code_len,
                **kwargs
            )
            html += '<span class="input-group-addon" style=padding:0;"><img %s><span>' % self.html_params(
                id='%s_img' % field.id,
                src=url_for('verify_code', key=field.key),
                data_src=url_for('verify_code', key=field.key),
                style="cursor:pointer",
                onclick="$(this).attr('src', '" + url_for('verify_code', key=field.key) + "&t=' + Math.random());",
            )
            html += '</div>'
        return HTMLString(html)


class UEditor(object):

    html_params = staticmethod(html_params)

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', 'text/plain')
        kwargs.setdefault('style', 'margin-right:-10px;height:360px;')
        kwargs['class'] = ''
        return HTMLString(
            '<script %s>%s</script><script>var ue = UE.getEditor("%s");</script>' % (
                self.html_params(name=field.name, **kwargs),
                text_type(field._value()),
                field.name,
            )
        )


class MDEditor(object):

    html_params = staticmethod(html_params)

    def __call__(self, field, **kwargs):
        return HTMLString(
            '<script %s>%s</script><script>var um = UM.getEditor("%s");</script>' % (
                self.html_params(name=field.name, **kwargs),
                text_type(field._value()),
                field.name,
            )
        )


class KListWidget(object):

    def __init__(self, html_tag='ul', sub_tag='li', sub_startswith='sub_', prefix_label=True):
        self.html_tag = html_tag
        self.sub_tag = sub_tag
        self.sub_startswith = sub_startswith
        self.prefix_label = prefix_label

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        sub_kwargs = dict((k[4:],v) for k, v in kwargs.iteritems() if k.startswith(self.sub_startswith))
        kwargs = dict(filter(lambda x: not x[0].startswith(self.sub_startswith), kwargs.iteritems()))
        sub_html = '%s %s' % (self.sub_tag, html_params(**sub_kwargs))
        html = ['<%s %s>' % (self.html_tag, html_params(**kwargs))]
        for subfield in field:
            if self.prefix_label:
                html.append('<%s>%s %s</%s>' % (sub_html, subfield.label, subfield(), self.sub_tag))
            else:
                html.append('<%s>%s %s</%s>' % (sub_html, subfield(), subfield.label, self.sub_tag))
        html.append('</%s>' % self.html_tag)
        return HTMLString(''.join(html))


class FileInput(object):

    template = """
        <div>
            <i class="icon-file"></i>%(filename)s
        </div>
        <div class="checkbox">
            <label>
                <input name="%(name)s-delete" type="checkbox" value="true"> 删除
            </label>
        </div>
    """

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.pop('class', None)
        kwargs.setdefault('style', 'margin: 10px 0;')

        placeholder = ''
        if field.data and field.data.filename:
            placeholder = self.template % dict(name=field.name, filename=field.data.filename)

        return HTMLString('%s<input %s>' % (placeholder, 
            html_params(name=field.name, type='file', **kwargs)))


class ImageInput(object):

    template = """
        <a href="%(thumb)s" target="_blank">
            <div class="image-thumbnail">
                <img src="%(thumb)s">
            </div>
        </a>
        <div class="checkbox">
            <label>
                <input name="%(name)s-delete" type="checkbox" value="true"> 删除 %(filename)s
            </label>
        </div>
    """

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.pop('class', None)
        kwargs.setdefault('style', 'margin: 10px 0;')

        placeholder = ''
        if field.data and hasattr(field.data, 'link') and field.data.link:
            placeholder = self.template % dict(
                thumb=field.data.link, 
                name=field.name,
                filename=field.data.filename,
            )

        return HTMLString('%s<input %s>' % (placeholder, 
            html_params(name=field.name, type='file', **kwargs)))


class AreaInput(object):

    template = (
        '<div %s><div class="col-xs-4" style="padding: 0 8px 0 0;"><select %s></select></div>'
        '<div class="col-xs-4" style="padding: 0 8px"><select %s></select></div>'
        '<div class="col-xs-4" style="padding: 0 0 0 8px;"><select %s></select></div>'
        '<script type="text/javascript">area.init("%s", "%s", "%s", "%s")</script>'
        '<div class="clearfix"></div></div>'
    )

    def __call__(self, field, **kwargs):
        datas = (field.data or '').split('|')
        if len(datas) == 3:
            province, city, county = datas
        else:
            province, city, county = '', '', ''
        province_name = '%s_province' % field.name
        city_name = '%s_city' % field.name
        county_name = '%s_county' % field.name
        return HTMLString(self.template % (
            html_params(id=field.name),
            html_params(id=province_name, name=province_name, **kwargs),
            html_params(id=city_name, name=city_name, **kwargs),
            html_params(id=county_name, name=county_name, **kwargs),
            field.name, province, city, county,
        ))


class WangEditor(TextArea):

    def __call__(self, field, **kwargs):
        kwargs.setdefault('style', 'height:480px;')
        script = """<script type="text/javascript">
            $(function() {
                var editor = $('#%s').wangEditor({
                    uploadImgComponent: $('#uploadContainer'),
                });
                window.WEditor = editor;
            });
        </script>""" % field.name
        return super(WangEditor, self).__call__(field, **kwargs) + script

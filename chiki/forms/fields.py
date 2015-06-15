# coding: utf-8
from datetime import datetime
from flask import current_app
from wtforms.fields import Field, StringField, SelectField, DateTimeField
from wtforms.fields import FileField as _FileField
from wtforms.widgets import RadioInput
from wtforms.validators import ValidationError
from wtforms.utils import unset_value
from .widgets import VerifyCode, UEditor, KListWidget
from .widgets import FileInput, ImageInput, AreaInput
from ..verify import get_verify_code, validate_code

__all__ = [
    'VerifyCodeField', 'KDateField', 'KRadioField', 'UEditorField',
    'FileField', 'ImageField', 'AreaField',
]


class VerifyCodeField(Field):

    widget = VerifyCode()

    def __init__(self, label=None, key='verify_code', 
            hidden=False, invalid_times=1, code_len=0, **kwargs):
        super(VerifyCodeField, self).__init__(label, **kwargs)
        self.key = key
        self.invalid_times = invalid_times
        self.hidden = hidden
        self.code_len = code_len if code_len > 0 else current_app.config.get('VERIFY_CODE_LEN', 4)
        self.code, self.times = get_verify_code(key, code_len=self.code_len)
        self._refresh = False

    def process_data(self, value):
        if self.hidden == True:
            self.data = self.code
        else:
            self.data = ''

    def process_formdata(self, valuelist):
        if not valuelist or not valuelist[0]:
            self.data = ''
        else:
            self.data = valuelist[0]

    def _value(self):
        return self.data

    def need_refresh(self):
        return self._refresh

    def validate(self, field, extra_validators=tuple()):
        self.errors = list(self.process_errors)
        if self.data.lower() != self.code.lower():
            self.times += 1
            validate_code(self.key)
            self.errors.append(u'验证码错误')

        if self.times >= self.invalid_times:
            self._refresh = True
            self.code, self.times = get_verify_code(self.key, 
                refresh=True, code_len=self.code_len)
            self.errors.append(u'验证码已失效')

        return len(self.errors) == 0


class KRadioField(SelectField):
    widget = KListWidget(html_tag='div', sub_tag='label', prefix_label=False)
    option_widget = RadioInput()


class KDateField(DateTimeField):

    def __init__(self, label=None, validators=None, format='%Y-%m-%d', allow_null=False, **kwargs):
        super(KDateField, self).__init__(label, validators, format, **kwargs)
        self.allow_null = allow_null

    def _value(self):
        if self.raw_data:
            return ' '.join(self.raw_data)
        else:
            if self.data and type(self.data) in (str, unicode):
                return self.data
            return self.data and self.data.strftime(self.format) or ''

    def process_formdata(self, valuelist):
        if valuelist:
            date_str = ' '.join(valuelist)
            if date_str:
                try:
                    self.data = datetime.strptime(date_str, self.format)
                except ValueError:
                    self.data = None
                    raise ValueError(self.gettext('Invalid date/time input'))
            else:
                self.data = None
                if not self.allow_null:
                    raise ValueError(self.gettext('Invalid date/time input'))


class UEditorField(StringField):
    widget = UEditor()


class FileField(_FileField):

    widget = FileInput()

    def __init__(self, max_size=None, allows=None, **kwargs):
        self.delete = False
        self.max_size = max_size
        self.allows = allows
        super(FileField, self).__init__(**kwargs)

    def pre_validate(self, form, extra_validators=tuple()):
        if not self.data:
            return

        format = self.data.filename.split('.')[-1]
        if self.allows and format not in self.allows:
            raise ValidationError(u'%s 格式不支持上传' % format)

        if self.max_size and self.data.content_length > self.max_size:
            raise ValidationError(u'文件太大(%d/%d)' % (
                self.max_size, self.data.content_length))

    def process(self, formdata, data=unset_value):
        self.process_errors = []
        if data is unset_value:
            try:
                data = self.default()
            except TypeError:
                data = self.default

        self.object_data = data

        try:
            self.process_data(data)
        except ValueError as e:
            self.process_errors.append(e.args[0])

        if formdata:
            if self.name in formdata:
                self.raw_data = formdata.getlist(self.name)
            else:
                self.raw_data = []
            self.process_formdata(self.raw_data)

            key = '%s-delete' % self.name
            if formdata.get(key) == 'true':
                self.delete = True

    def is_empty(self):
        if self.data:
            self.data.stream.seek(0)
            first_char = self.data.stream.read(1)
            self.data.stream.seek(0)
            return not bool(first_char)
        return True

    def populate_obj(self, obj, name):
        if self.data and not self.is_empty():
            setattr(obj, name, self.data)
        elif self.delete:
            setattr(obj, name, None)


class ImageField(FileField):

    widget = ImageInput()


class AreaField(Field):

    widget = AreaInput()

    def process(self, formdata, data=unset_value):
        self.process_errors = []
        if data is unset_value:
            try:
                data = self.default()
            except TypeError:
                data = self.default

        self.object_data = data

        try:
            self.process_data(data)
        except ValueError as e:
            self.process_errors.append(e.args[0])

        if formdata:
            area = []
            for field in ['province', 'city', 'county']:
                name = '%s_%s' % (self.name, field)
                data = formdata.get(name, '').strip()
                if data:
                    area.append(data)
            if len(area) == 3:
                self.data = '|'.join(area)
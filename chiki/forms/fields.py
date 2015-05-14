# coding: utf-8
from flask import current_app
from wtforms.fields import Field, StringField, SelectField, DateTimeField
from wtforms.widgets import RadioInput
from .widgets import VerifyCode, UEditor, KListWidget
from ..verify import get_verify_code, validate_code

__all__ = [
	'VerifyCodeField', 'KDateField', 'KRadioField', 'UEditorField',
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
			return self.data and time.strftime(self.format, time.localtime(self.data)) or ''

	def process_formdata(self, valuelist):
		if valuelist:
			date_str = ' '.join(valuelist)
			if date_str:
				try:
					self.data = time.strptime(date_str, self.format)
				except ValueError:
					self.data = None
					raise ValueError(self.gettext('Invalid date/time input'))
			else:
				self.data = None
				if not self.allow_null:
					raise ValueError(self.gettext('Invalid date/time input'))


class UEditorField(StringField):
	widget = UEditor()
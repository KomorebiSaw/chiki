# coding: utf-8
from wtforms.fields import Field
from wtforms.fields import FileField as _FileField
from wtforms.utils import unset_value
from wtforms.validators import ValidationError
from .widgets import FileInput, ImageInput, AreaInput


class FileField(_FileField):

	widget = FileInput()

	def __init__(self, size=None, allows=None, **kwargs):
		self.size = size
		self.allows = allows
		super(FileField, self).__init__(**kwargs)

	def pre_validate(self, form, extra_validators=tuple()):
		if not self.data:
			return

		format = self.data.filename.split('.')[-1]
		if self.allows and format not in self.allows:
			raise ValidationError(u'%s 格式不支持上传' % format)

		if self.size and value.upload.content_length > self.size:
			raise ValidationError(u'文件太大(%d/%d)' % (self.size, value.upload.content_length))


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
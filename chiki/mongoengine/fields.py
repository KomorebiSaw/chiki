# coding: utf-8
import os
import time
import traceback
import shutil
import hashlib
from flask import current_app, url_for
from mongoengine import signals
from mongoengine.base.fields import BaseField
from werkzeug.datastructures import FileStorage

__all__ = [
	'XFileField', 'XImageField', 'AreaField',
]
DEFAULT_ALLOWS = ['txt', 'bz2', 'gz', 'tar', 'zip', 'rar', 'apk']
DEFAULT_IMAGE_ALLOWS = ['jpg', 'jpeg', 'png', 'gif', 'bmp']


def is_empty(file_object):
	file_object.seek(0)
	first_char = file_object.read(1)
	file_object.seek(0)
	return not bool(first_char)


def is_empty_folder(folder):
	for root, dirs, files in os.walk(folder):
		if len(dirs) == 0 and len(files) == 0:
			return True
		return False
		

def makedir(pathname):
	dirname = os.path.dirname(pathname)
	if not os.path.exists(dirname):
		makedir(dirname)
		os.mkdir(dirname)


class FileProxy(object):
	
	def __init__(self, instance, filename=''):
		self.instance = instance
		self.filename = filename

	@property
	def path(self):
		if self.filename:
			return self.instance.get_pathname(self.filename)

	@property
	def md5(self):
		path = self.path
		if path and os.path.isfile(path):
			m = hashlib.md5()
			with open(path, 'rb') as fd:
				m.update(fd.read())
			return m.hexdigest()
		return ''

	@property
	def size(self):
		return 0

	@property
	def url(self):
		if self.filename:
			return self.instance.get_url(self.filename)
		return ''

	@property
	def web_url(self):
		if self.filename:
			return self.instance.get_web_url(self.filename)
		return ''

	def process(self, upload):
		if upload:
			self.delete()
			if not self.filename:
				filename = self.instance.get_filename(upload.filename)
			else:
				filename = self.filename
			pathname = self.instance.get_pathname(filename)
			makedir(pathname)
			upload.save(pathname)
			self.filename = filename

	def delete(self):
		try:
			self._delete()
		except:
			traceback.print_exc()

	def _delete(self):
		if self.filename:
			pathname = self.instance.get_pathname(self.filename)
			if os.path.isfile(pathname):
				os.remove(pathname)
				folder = os.path.dirname(pathname)
				if is_empty_folder(folder):
					shutil.rmtree(folder)

	def __unicode__(self):
		return self.filename or ''


class XFileField(BaseField):

	proxy_class = FileProxy
	default_allows = DEFAULT_ALLOWS

	def __init__(self, path='', size=None, allows=None, **kwargs):
		self.path = path
		self.size = size
		self.allows = allows or self.default_allows
		super(XFileField, self).__init__(**kwargs)

	def register_signals(self, instance):
		if not hasattr(self, '_instance') and instance is not None:
			self._instance = instance
			signals.pre_delete.connect(self.pre_delete, sender=self._instance.__class__)

	def pre_delete(self, sender, document, **kwargs):
		_file = document._data.get(self.name)
		if isinstance(_file, self.proxy_class):
			_file.delete()

	def __get__(self, instance, owner):
		if instance is None:
			return self

		_file = instance._data.get(self.name)
		if not isinstance(_file, self.proxy_class) or _file is None:
			_file = self.proxy_class(self, _file)
			instance._data[self.name] = _file

		return instance._data[self.name]

	def __set__(self, instance, value):
		self.register_signals(instance)

		key = self.name
		if isinstance(value, FileStorage):
			_file = instance._data.get(self.name, self.proxy_class(self))
			if not is_empty(value.stream):
				_file.process(value)
			instance._data[key] = _file
		else:
			instance._data[key] = value
		instance._mark_as_changed(key)

	def get_filename(self, filename):
		format = filename.split('.')[-1]
		stime = time.strftime('%Y%m%d/%H%M%S')

		i = 0
		while True:
			filename = '%s%d.%s' % (stime, i, format)
			pathname = self.get_pathname(filename)
			if not os.path.exists(pathname):
				return filename
			i += 1

	def get_pathname(self, filename):
		return os.path.join(self.path, filename)

	def get_url(self, filename):
		return url_for('uploads', filename=filename)

	def get_web_url(self, filename):
		TPL = current_app.config.get('UPLOAD_URL_TPL')
		return TPL % filename

	def to_mongo(self, value):
		if isinstance(value, self.proxy_class):
			return value.filename

		return value

	def to_python(self, value):
		return self.proxy_class(self, value)


class ImageProxy(object):
	pass


class XImageField(XFileField):
	
	default_allows = DEFAULT_IMAGE_ALLOWS


class AreaField(BaseField):
	pass
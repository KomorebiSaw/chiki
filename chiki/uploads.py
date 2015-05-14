# coding: utf-8
import os
from flask import send_from_directory

__all__ = [
	'Uploads', 'init_uploads',
]


class Uploads(object):

	def __init__(self, app=None):
		if app is not None:
			self.init_app(app)

	def init_app(self, app):
		UPLOAD_FOLDER = app.config.get('UPLOAD_FOLDER')

		@app.route('/uploads/<path:filename>', endpoint='uploads')
		def uploads(filename):
			return send_from_directory(UPLOAD_FOLDER, filename)


def init_uploads(app):
	uploads = Uploads()
	uploads.init_app(app)
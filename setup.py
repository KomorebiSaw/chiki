# coding: utf-8
import re
import os
from setuptools import setup, find_packages


def fpath(name):
	return os.path.join(os.path.dirname(__file__), name)


def read(fname):
	return open(fpath(fname)).read()


file_text = read(fpath('chiki/__init__.py'))

def grep(attrname):
	pattern = r"{0}\W*=\W*'([^']+)'".format(attrname)
	strval, = re.findall(pattern, file_text)
	return strval


setup(
	name='chiki',
	version=grep('__version__'),
	url='https://www.chiki.org/',
	author=grep('__author__'),
	author_email=grep('__email__'),
	description='Common libs of flask web develop',
	packages=find_packages(),
	include_package_data=True,
	zip_safe=False,
	platforms='any',
	install_requires=[
		'Flask==0.10.1',
		'Flask-Admin==1.1.0',
		'Flask-BabelEx==0.9.2',
		'flask-mongoengine==0.7.1',
		'Flask-WTF==0.11',
		'Jinja2==2.7.3',
		'WTForms==2.0.2',
		'Flask-Script==2.0.5',
		'wheezy.captcha==0.1.44',
		'Pillow==2.7.0',
    ],
)
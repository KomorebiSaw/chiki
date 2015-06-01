#　coding: utf-8
from flask import request


def message(msg, style='info'):
	return msg


def is_ajax():
	return request.headers.get('X-Requested-With') == 'XMLHttpRequest' \
		or request.args.get('ajax') == 'true'
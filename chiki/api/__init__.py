# coding: utf-8


def api_success(**kwargs):
	kwargs['code'] = 0
	return kwargs
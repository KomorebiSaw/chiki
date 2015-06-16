# coding: utf-8
from __future__ import unicode_literals
from flask.ext.restful import abort as _abort

_code = 0
def code(n=None):
	if not n or type(n) != int:
		n = _code + 1
	globals()['_code'] = n
	return n


_keys = {}
_msgs = {}
def M(**kwargs):
	for key, n in kwargs.iteritems():
		globals()[key] = code(n)
		_keys[globals()[key]] = key
		_msgs[globals()[key]] = key if type(n) == int else n


def abort(code, **kwargs):
	_abort(200, code=code, key=_keys[code], msg=_msgs[code], **kwargs)


M(COMMON_START=20000)
M(SERVER_ERROR='系统出错')
M(ACCESS_DENIED='非法操作')
M(ARGS_ERROR='参数错误')
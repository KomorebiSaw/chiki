# coding: utf-8
import time
import traceback
from datetime import datetime, date
from flask import jsonify, current_app, request

__all__ = [
    'strip', 'json_success', 'json_error', 
    'datetime2best', 'time2best', 'today',
    'err_logger', 'parse_spm', 'is_empty', 'get_ip',
    'is_ajax', 'is_ajax', 'str2datetime',
]


def today():
    return datetime.strptime(str(date.today()),'%Y-%m-%d')


def strip(val, *args):
    if not val:
        return val

    if isinstance(val, dict):
        return dict((x, strip(y) if x not in args else y) for x, y in val.iteritems())
    if isinstance(val, list):
        return list(strip(x) for x in val)
    if hasattr(val, 'strip'):
        return val.strip()
    return val


def json_success(**kwargs):
    kwargs['code'] = 0
    return jsonify(kwargs)


def json_error(**kwargs):
    kwargs['code'] = -1
    return jsonify(kwargs)


def datetime2best(input):
    return time2best(time.mktime(input.timetuple()))


def time2best(input):
    if type(input) == datetime:
        return datetime2best(input)
        
    now = max(time.time(), input) + 8 * 3600
    tmp = input + 8 * 3600
    if tmp + 86400 < now // 86400 * 86400:
        if time.strftime('%Y', time.localtime(input)) == time.strftime('%Y', time.localtime()):
            return time.strftime('%m.%d', time.localtime(input))
        return time.strftime(u'%y年%m月', time.localtime(input))
    elif tmp < now // 86400 * 86400:
        return u'昨天'

    offset = now - tmp
    hours = offset // 3600
    if hours > 0:
        if hours >= 12: 
            hours = 12
        elif hours > 6:
            hours = hours // 2 * 2
        return u'%s小时前' % int(hours)

    minutes = offset // 60
    if minutes > 1:
        if minutes >= 30:
            minutes = 30
        elif minutes >= 10:
            minutes = minutes // 10 * 10
        elif minutes >= 5:
            minutes = 5
        return u'%s分钟前' % int(minutes)

    return u'刚刚'


def err_logger(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            current_app.logger.error(traceback.format_exc())
    return wrapper


def parse_spm(spm):
    if spm:
        spm = spm.replace('unknown', '0')
    if spm and re.match(r'^(\d+\.)+\d+$', spm):
        res = map(lambda x: int(x), spm.split('.'))
        while len(res) < 5: res.append(0)
        return res[:5]
    return 0, 0, 0, 0, 0


def is_empty(fd):
    fd.seek(0)
    first_char = fd.read(1)
    fd.seek(0)
    return not bool(first_char)


def get_ip():
    if 'Cdn-Real-Ip' in request.headers:
        return request.headers['Cdn-Real-Ip']
    if 'X-Real-Forwarded-For' in request.headers:
        return request.headers['X-Real-Forwarded-For'].split(',')[0]
    if 'X-FORWARDED-FOR' in request.headers:
        return request.headers['X-FORWARDED-FOR'].split(',')[0]
    return request.headers.get('X-Real-Ip') or request.remote_addr


def is_ajax():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest' \
        or request.args.get('is_ajax', 'false') == 'true'


def str2datetime(datestr):
    try:
        return datetime.strptime(datestr, '%Y-%m-%d %H:%M:%s')
    except ValueError:
        return datetime.min

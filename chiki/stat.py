# coding: utf-8
import sys
import time
import functools
import inspect
from chiki.contrib.common import StatLog
from datetime import datetime, timedelta
from flask import request
from flask.ext.admin import expose
from .utils import json_success, get_module


def get_date_ranger(date_start, date_end):
    dates = []
    start = datetime.strptime(date_start, '%Y-%m-%d')
    end = datetime.strptime(date_end, '%Y-%m-%d')
    size = (end - start).days

    if size >= 0:
        i = 0
        while i < size + 1:
            dates.append((start + timedelta(days=i)).strftime('%Y-%m-%d'))
            i += 1
    return dates


def get_date(key='day'):
    day = request.args.get(key, '')
    try:
        datetime.strptime(day, '%Y-%m-%d')
    except ValueError:
        day = time.strftime('%Y-%m-%d')
    return day


def get_dates(stat=True, start_key='start', end_key='end'):
    start = request.args.get(start_key, '')
    end = request.args.get(end_key, '')

    try:
        datetime.strptime(start, '%Y-%m-%d')
        datetime.strptime(end, '%Y-%m-%d')
    except ValueError:
        start = (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')
        end = datetime.now().strftime('%Y-%m-%d')

    if stat is True:
        days = get_date_ranger(start, end)
        if len(days) == 0:
            start = (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')
            end = datetime.now().strftime('%Y-%m-%d')

    return start, end


def get_value_list(key, days, tid=None):
    query = dict(key=key, day__in=days)
    if tid:
        query['tid'] = tid

    length = len(days)
    value_list = [0 for i in range(length)]
    items = StatLog.objects(**query)
    for item in items:
        value_list[days.index(item.day)] = item.value
    return value_list


def get_hour_list(key, day, tid=None, hour=23):
    query = dict(key=key, day=day)
    if tid:
        query['tid'] = tid

    items = StatLog.objects(**query)
    values = [0 for i in range(hour + 1)]
    for item in items:
        if item.hour <= hour:
            values[item.hour] = item.value
    return values


def hour_value_list(day, key, *args, **kwargs):
    return get_hour_list(key, day, **kwargs)


def init_stat(cls, key, subs, tpl):
    """ 初始化统计 """

    @expose('/' if key == 'index' else '/%s' % key)
    def index(self):
        now = datetime.now()
        start, end = get_dates(stat=True)
        month_start = (now - timedelta(days=30)).strftime('%Y-%m-%d')
        week_start = (now - timedelta(days=6)).strftime('%Y-%m-%d')
        yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
        today = now.strftime('%Y-%m-%d')
        return self.render(tpl,
            start=start, end=end, month_start=month_start, month_end=today,
            week_start=week_start, week_end=today, yesterday=yesterday,
            today=today, data_url=self.get_url('.%s_data' % key))

    def get_series(sub, prefix, axis, value_list):
        res = []
        for item in sub.get('series'):
            value = value_list('%s%s' % (prefix, item.get('key')), axis)
            handle = item.get('handle')
            if callable(handle):
                value = [handle(x) for x in value]
            res.append(dict(name=item.get('name'), data=value))
        return res

    def common_data(prefix, subtitle, axis, value_list):
        items = []
        subtitle += '<br>'
        for sub in subs:
            item = dict(
                title=sub.get('title'),
                suffix=sub.get('suffix'),
                axis=axis,
                series=get_series(sub, prefix, axis, value_list),
            )
            totals = []
            tpl = '<span>%s: %d%s</span>'
            for ser in item['series']:
                totals.append(tpl % (ser['name'], sum(ser['data']), sub.get('suffix')))
            item['subtitle'] = subtitle + ' - '.join(totals)
            items.append(item)
        return json_success(items=items)

    def hour_data():
        day = get_date()
        hours = ['%02d时' % i for i in range(24)]
        value_list = functools.partial(hour_value_list, day)
        return common_data('hour_', day, hours, value_list)

    def date_data():
        start, end = get_dates(True)
        days = get_date_ranger(start, end)
        return common_data('date_', '%s 至 %s' % (start, end), days, get_value_list)

    @expose('/data' if key == 'index' else '/%s/data' % key)
    def data(self):
        model = request.args.get('model', 'day')
        if model == 'day':
            return date_data()
        return hour_data()

    setattr(cls, key, index)
    setattr(cls, '%s_data' % key, data)


def statistics(tpl='admin/stat.html'):
    def wrapper(cls):
        datas = getattr(cls, 'datas', None)
        if datas:
            for key, subs in datas.iteritems():
                init_stat(cls, key, subs, tpl)
        return type(cls.__name__, (cls,), {})
    return wrapper


class Stat(object):
    """ 统计助手 """

    def __init__(self):
        self.items = []
        self.start = datetime(2016, 1, 1)
        self.minutes = 1

    def _save(self, _key, _day, _hour, _value, **kwargs):
        if callable(_value):
            _value = _value(**kwargs)

        # print '%s: %d' % (_key, _value)
        StatLog.objects(key=_key, day=_day, hour=_hour).update(
            set__value=_value,
            set__modified=datetime.now(),
            set_on_insert__created=datetime.now(),
            upsert=True,
        )

    def save(self, _key, _day, _start, _end, _value, _hour=0, field='created', **kwargs):
        kwargs.setdefault('%s__gte' % field, _start)
        kwargs.setdefault('%s__lt' % field, _end)
        return self._save(_key, _day, _hour, _value=_value, **kwargs)

    def stat(self, _key, _model, _query=lambda x: x.count(), _handle=lambda x: x, **kwargs):
        self.items.append(dict(
            key=_key,
            model=_model,
            query=_query,
            handle=_handle,
            kwargs=kwargs,
        ))

    def count(self, _key, _model, **kwargs):
        return self.stat(_key, _model, **kwargs)

    def sum(self, _key, _model, _sub, **kwargs):
        return self.stat(_key, _model, _query=lambda x: x.aggregate_sum(_sub), **kwargs)

    def distinct(self, _key, _model, _sub, **kwargs):
        return self.stat(_key, _model, _query=lambda x: x.distinct(_sub), _handle=len, **kwargs)

    def one(self, key, day, start, end, hour=0):
        for item in self.items:
            value = lambda **x: item['handle'](item['query'](item['model'].objects(**x)))
            self.save('%s_%s' % (key, item['key']), day, start, end, value, hour, **item['kwargs'])

    def day(self, day):
        start = datetime.strptime(str(day).split(' ')[0], '%Y-%m-%d')
        end = datetime.strptime(str(day + timedelta(days=1)).split(' ')[0], '%Y-%m-%d')
        self.one('date', day.strftime('%Y-%m-%d'), start, end)

    def hour(self, now, day=True):
        start = now - timedelta(minutes=self.minutes)
        start = start - timedelta(minutes=start.minute, seconds=start.second, microseconds=start.microsecond)
        end = start + timedelta(hours=1)
        self.one('hour', start.strftime('%Y-%m-%d'), start, end, hour=start.hour)
        if day:
            self.day(start)

    def all(self):
        now = datetime.now()
        while now >= self.start:
            print 'stat:', now
            self.hour(now, day=now.hour == 0)
            now -= timedelta(hours=1)

    def run(self, start=datetime(2016, 1, 1), minutes=1):
        self.start = start
        self.minutes = minutes

        def run_stat(model='last'):
            if model in ['last', 'simple']:
                start = time.time()
                print 'stat hour:', datetime.now(),
                self.hour(datetime.now())
                print time.time() - start
            elif model == 'all':
                self.all()

        return run_stat

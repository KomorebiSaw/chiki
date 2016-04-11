# coding: utf-8
import time
from chiki.contrib.common import StatLog
from datetime import datetime, timedelta
from flask import request


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

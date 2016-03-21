# coding: utf-8
import time
from collections import defaultdict
from chiki import strip, get_version, get_os
from chiki.api import success
from flask import current_app, request, url_for
from flask.ext.login import current_user, login_required
from flask.ext.restful import Resource, reqparse
from chiki.api.const import *
from chiki.utils import parse_spm
from chiki.base import db
from chiki.contrib.common.models import (
    Enable, Item, APIItem, TPLItem, AndroidVersion,
    ActionItem, SlideItem, OptionItem
)


class CommonAPI(Resource):

    def get(self):
        res = dict(apis={}, tpls={}, actions=defaultdict(list), options={})
        version = get_version()

        apis = APIItem.objects.all()
        for api in apis:
            res['apis'][api.key] = api.detail

        for option in OptionItem.objects.all():
            res['options'][option.key] = option.value
        res['options']['uuid'] = '0'
        res['options']['channel'] = '0'

        tpls = TPLItem.objects(enable__in=Enable.get()).order_by('sort')
        for tpl in tpls:
            res['tpls'][tpl.key] = dict(
                key=tpl.key,
                name=tpl.name,
                url=tpl.tpl.link,
                modified=str(tpl.modified),
            )

        query = db.Q(enable__in=Enable.get())
        if get_os() == 2:
            query = query & (db.Q(android_version__lte=version) | db.Q(android_version=None)) & \
                (db.Q(android_version_end__gte=version) | db.Q(android_version_end=None))
        elif get_os() == 1:
            query = query & (db.Q(ios_version__lte=version) | db.Q(ios_version=None)) & \
                (db.Q(ios_version_end__gte=version) | db.Q(ios_version_end=None))
        if not current_user.is_authenticated():
            query = query & (db.Q(login_show=False) | db.Q(login_show=None))

        actions = ActionItem.objects(enable__in=Enable.get()).order_by('sort')
        for action in actions:
            if action.module and action.module.key:
                res['actions'][action.module.key].append(action.detail)

        slides = SlideItem.objects(enable__in=Enable.get()).order_by('sort')
        for slide in slides:
            if slide.module and slide.module.key:
                res['actions'][slide.module.key].append(slide.detail)

        return res


class AndroidAPI(Resource):

    def get(self):
        item = AndroidVersion.objects(enable__in=Enable.get()).order_by('-id').first()
        if item:
            spm = parse_spm(request.args.get('spm'))
            url = item.url or current_app.config.get('HOST') + '/android/latest.html?channel=%d' % (spm[2] or 1001)
            return success(
                version=item.version,
                code=item.id,
                log=item.log,
                url=url,
                force=item.force,
                date=str(item.created).split(' ')[0],
            )
        abort(SERVER_ERROR)


def init(api):
    api.add_resource(CommonAPI, '/common')
    api.add_resource(AndroidAPI, '/android/latest')
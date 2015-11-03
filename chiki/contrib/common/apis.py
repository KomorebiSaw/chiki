# coding: utf-8
import time
from chiki import strip
from chiki.api import success
from flask import current_app, request, url_for
from flask.ext.login import current_user, login_required
from flask.ext.restful import Resource, reqparse
from chiki.api.const import *
from chiki.utils import parse_spm
from chiki.contrib.common.models import (
    Enable, Item, APIItem, TPLItem, AndroidVersion, 
    ActionItem, SlideItem, 
)


class CommonAPI(Resource):

    def get(self):
        res = dict(apis={}, tpls={}, actions={}, slides={}, cache=0)

        apis = APIItem.objects.all()
        for api in apis:
            if api.key == 'common':
                res['cache'] = api.cache
            else:
                res['apis'][api.key] = api.detail

        tpls = TPLItem.objects(enable__in=Enable.get()).order_by('sort')
        for tpl in tpls:
            res['tpls'][tpl.key] = dict(name=tpl.name, url=tpl.tpl.link, modified=str(tpl.modified))

        actions = ActionItem.objects(enable__in=Enable.get()).order_by('sort')
        for action in actions:
            if action.module not in res['actions']:
                res['actions'][action.module] = list()
            res['actions'][action.module].append(action.detail)

        slides = SlideItem.objects(enable__in=Enable.get()).order_by('sort')
        for slide in slides:
            if slide.module not in res['actions']:
                res['actions'][slide.module] = list()
            res['actions'][slide.module].append(slide.detail)

        res['backup_host'] = Item.data('backup_host')
        res['channel'] = 1001
        res['uuid'] = current_user.id if current_user.is_authenticated() else 0
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
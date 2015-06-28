# coding: utf-8
import re
import sys
import difflib
from flask import current_app, request
from flask.signals import got_request_exception
from flask.ext.restful import Api as _Api
from flask.ext.restful.utils import error_data
from werkzeug.http import HTTP_STATUS_CODES

__all__ = [
    'api', 'success',
]


class Api(_Api):

    def handle_error(self, e):
        got_request_exception.send(current_app._get_current_object(), exception=e)

        if not hasattr(e, 'code') and current_app.propagate_exceptions:
            exc_type, exc_value, tb = sys.exc_info()
            if exc_value is e:
                raise
            else:
                raise e
        code = getattr(e, 'code', 500)
        data = getattr(e, 'data', error_data(code))
        headers = {}

        if code >= 500:

            # There's currently a bug in Python3 that disallows calling
            # logging.exception() when an exception hasn't actually be raised
            if sys.exc_info() == (None, None, None):
                current_app.logger.error("Internal Error")
            else:
                current_app.logger.exception("Internal Error")

        help_on_404 = current_app.config.get("ERROR_404_HELP", True)
        if code == 404 and help_on_404 and ('message' not in data or
                                            data['message'] == HTTP_STATUS_CODES[404]):
            rules = dict([(re.sub('(<.*>)', '', rule.rule), rule.rule)
                          for rule in current_app.url_map.iter_rules()])
            close_matches = difflib.get_close_matches(request.path, rules.keys())
            if close_matches:
                # If we already have a message, add punctuation and continue it.
                if "message" in data:
                    data["message"] += ". "
                else:
                    data["message"] = ""

                data['message'] += 'You have requested this URI [' + request.path + \
                                   '] but did you mean ' + \
                                   ' or '.join((
                                       rules[match] for match in close_matches)
                                   ) + ' ?'

        if code == 405:
            headers['Allow'] = e.valid_methods

        error_cls_name = type(e).__name__
        if error_cls_name in self.errors:
            custom_data = self.errors.get(error_cls_name, {})
            code = custom_data.get('status', 500)
            data.update(custom_data)

        if code == 406 and self.default_mediatype is None:
            supported_mediatypes = list(self.representations.keys())
            fallback_mediatype = supported_mediatypes[0] if supported_mediatypes else "text/plain"
            resp = self.make_response(
                data,
                code,
                headers,
                fallback_mediatype = fallback_mediatype
            )
        else:
            if code == 400 and current_app.config.get('CHANGE_400_TO_200'):
                code = 200
            resp = self.make_response(data, code, headers)

        if code == 401:
            resp = self.unauthorized(resp)
        return resp


api = Api()


def success(**kwargs):
    if kwargs.get('__external'):
        kwargs.setdefault('code', 0)
        kwargs.setdefault('key', 'SUCCESS')
        return dict(**kwargs)
    return dict(code=0, key='SUCCESS', data=kwargs)
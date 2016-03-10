# coding: utf-8
from flask import request, url_for
from flask.ext.mongoengine.pagination import Pagination as _Pagination


class Pagination(_Pagination):

    def __init__(self, iterable, page, per_page, endpoint=None, **kwargs):
        super(Pagination, self).__init__(iterable, page, per_page)
        self.endpoint = endpoint if endpoint else request.endpoint
        self.kwargs = kwargs

    @property
    def has_pages(self):
        return self.pages > 1

    @property
    def next_link(self):
        if self.has_next:
            return self.get_link(self.next_num)
        return ''

    def get_link(self, page):
        return url_for(self.endpoint, page=page, per_page=self.per_page, **self.kwargs)

    def iter_links(self, pages=5, next=False, last=True):
        if last:
            yield '<<', self.get_link(1) if self.page > 1 else None
        if next:
            yield '<', self.get_link(self.prev_num) if self.has_prev else None

        start = max(1, self.page - (pages - 1) / 2)
        end = min(self.pages + 1, start + pages)
        start = max(1, end - pages)
        for i in range(start, end):
            yield i, self.get_link(i)

        if next:
            yield '>', self.get_link(self.next_num) if self.has_next else None
        if last:
            yield '>>', self.get_link(self.pages) if self.page < self.pages else None

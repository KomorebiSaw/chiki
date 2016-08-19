# coding: utf-8
import mongoengine
from flask.ext.admin.contrib.mongoengine.ajax import QueryAjaxModelLoader as _QueryAjaxModelLoader, DEFAULT_PAGE_SIZE


class QueryAjaxModelLoader(_QueryAjaxModelLoader):

    def __init__(self, name, model, **options):
        super(QueryAjaxModelLoader, self).__init__(name, model, **options)
        self.filter = options.get('filter')

    def get_list(self, term, offset=0, limit=DEFAULT_PAGE_SIZE):
        query = self.model.objects

        criteria = None
        for field in self._cached_fields:
            flt = {u'%s__icontains' % field.name: term}

            if not criteria:
                criteria = mongoengine.Q(**flt)
            else:
                criteria |= mongoengine.Q(**flt)

        if self.filter:
            if not criteria:
                criteria = self.filter
            else:
                criteria &= self.filter

        query = query.filter(criteria)

        if offset:
            query = query.skip(offset)

        return query.limit(limit).all()


def create_ajax_loader(model, name, field_name, opts):
    prop = getattr(model, field_name, None)

    if prop is None:
        raise ValueError('Model %s does not have field %s.' % (model, field_name))

    ftype = type(prop).__name__

    if ftype == 'ListField' or ftype == 'SortedListField':
        prop = prop.field
        ftype = type(prop).__name__

    if ftype != 'ReferenceField':
        raise ValueError('Dont know how to convert %s type for AJAX loader' % ftype)

    remote_model = prop.document_type
    return QueryAjaxModelLoader(name, remote_model, **opts)

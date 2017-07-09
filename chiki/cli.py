# coding: utf-8
import re
import os
import click
from datetime import datetime
from cookiecutter.main import cookiecutter


def search_item(path, items):
    for name in os.listdir(path):
        subpath = os.path.join(path, name)
        if os.path.isdir(subpath):
            search_item(subpath, items)
        elif subpath.rsplit('.', 1)[-1] in ['py', 'htm', 'html']:
            with open(subpath) as fd:
                subs = re.findall('(Item\.(?!set).+?\((.|\n)+?\))', fd.read())
                items += [re.sub(',\n +', ', ', sub[0]) for sub in subs]


def create_item():
    items = []
    name = os.popen('python setup.py --name').read()[:-1]
    search_item(name, items)
    search_item('templates', items)

    res = dict()
    for item in items:
        if "%" in item:
            item = "# " + item
        match = re.search(r'\([\'"](.*?)[\'"]', item)
        if match:
            res[match.group(1)] = item
        else:
            res[item] = item

    items = [x for _, x in sorted(res.iteritems(), key=lambda m: m[0])]

    path = os.path.join(name, 'services/init.py')
    content = """# coding: utf-8
from chiki.admin.common import documents
from chiki.contrib.common import Item


def init_items():
    pass


def init():
    pass


def clear_db():
    for name, doc in documents.iteritems():
        if not doc._meta['abstract'] and doc._is_document:
            doc.objects.delete()


def run(model='simple'):
    if model == 'clear_db':
        clear_db()

    init()
    init_items()
"""

    if os.path.isfile(path):
        with open(path) as fd:
            content = fd.read()

    items = "def init_items():\n    %s\n\n\n" % ('\n    '.join(items))
    content = re.sub(r"def init_items\(\):\n(.|\n)+?\n\n\n",
                     items, content)

    with open(path, 'w+') as fd:
        fd.write(content)


@click.command()
@click.argument('cmd')
def run(cmd):
    if cmd == 'item':
        create_item()


@click.command()
@click.argument('template')
@click.option(
    '--no-input', is_flag=True,
    help='Do not prompt for parameters and only use cookiecutter.json '
         'file content',
)
@click.option(
    '-c', '--checkout',
    help='branch, tag or commit to checkout after git clone',
)
@click.option('-a', '--api', is_flag=True, help='create the api server')
@click.option('-w', '--web', is_flag=True, help='create the web server')
def main(template, no_input, checkout, api, web):
    context = dict(today=datetime.now().strftime('%Y-%m-%d'))
    if api:
        context['has_api'] = True
    if web:
        context['has_web'] = True
    cookiecutter(template, checkout, no_input, extra_context=context)

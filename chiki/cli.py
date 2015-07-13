# coding: utf-8
from __future__ import unicode_literals

import click
from datetime import datetime
from cookiecutter.main import cookiecutter


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
    context=dict(today=datetime.now().strftime('%Y-%m-%d'))
    if api:
        context['has_api'] = True
    if web:
        context['has_web'] = True
    cookiecutter(template, checkout, no_input, extra_context=context)
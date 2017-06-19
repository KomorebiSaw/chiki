# coding: utf-8
from fabric.api import env, run, roles, task, settings
from .utils import xput


@roles('web')
@task
def nginx():
    with settings(user='root', password=env.sudo_password):
        xput('nginx/web.nginx.conf',
             '/etc/nginx/sites-enabled/%s.nginx.conf' % env.project)
        run('service nginx reload')


@roles('web')
@task
def nginx_upgrade():
    xput('files/upgrade.html', env.path)
    with settings(user='root', password=env.sudo_password):
        xput('nginx/web.upgrade.nginx.conf',
             '/etc/nginx/sites-enabled/%s.nginx.conf' % env.project)
        run('service nginx reload')


@roles('web')
@task
def nginx_remove():
    run('rm /etc/nginx/sites-enabled/%s.nginx.conf' % env.project)


@roles('front')
@task
def nginx_front(update=False):
    update = True if update in ['True', 'true', True] else False
    if update:
        run('apt-get update && apt-get install nginx -y')

    filename = '/etc/nginx/sites-enabled/%s.nginx.conf' % env.branch
    xput('nginx/front.nginx.conf', filename)
    run('service nginx reload')


# @roles('front')
# @task
# def nginx_upgrade(update=True):
#     if update:
#         run('apt-get update && apt-get install nginx -y')

#     filename = '/etc/nginx/sites-enabled/%s.nginx.conf' % env.branch
#     xput('nginx/upgrade.nginx.conf', filename)
#     run('service nginx reload')


@roles('puppet')
@task
def nginx_puppet(update=False):
    update = True if update in ['True', 'true', True] else False
    if update:
        run('apt-get update && apt-get install nginx -y')

    xput('nginx/puppet.nginx.conf',
         '/etc/nginx/sites-enabled/%s.nginx.conf' % env.project)
    run('service nginx reload')

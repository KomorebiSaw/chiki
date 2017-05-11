# coding: utf-8
import os
from fabric.api import cd, env, run, roles, task
from fabric.api import settings, local
from fabric.contrib.files import exists, append
from .nginx import nginx
from .server import restart, restart_back
from .utils import execute, xrun, xput


@task
def all():
    execute(init)
    execute(create_env)
    execute(deploy)
    execute(nginx)


def build():
    run('apt-get update')
    run(
        'apt-get install -y vim software-properties-common'
        ' python-setuptools nginx --force-yes'
        ' libmysqlclient-dev git gcc g++ unzip'
        ' python-virtualenv python-dev subversion curl'
        ' libxml2-dev libxslt1-dev libfreetype6-dev'
        ' libjpeg62 libpng3 libjpeg-dev libpng12-dev'
        ' libffi-dev libssl-dev'
    )
    run('easy_install pip supervisor')
    run('pip install virtualenvwrapper')

    run('sed -i "s/#   StrictHostKeyChecking ask/'
        'StrictHostKeyChecking no/g" /etc/ssh/ssh_config')


def create_user(name):
    if not exists('/home/%s' % name):
        run('echo "\n\n\n\n\nY\n" | adduser --disabled-password -q %s' % name)
        run('usermod -p $(openssl passwd -1 %s) %s' % (
            env.user_password, name))


@roles('web')
@task
def remove_user(name=None):
    if not name:
        name = env.user
    with settings(user='root', password=env.sudo_password):
        run('killall -u %s' % name)
        run('userdel %s' % name)
        run('rm -rf /home/%s' % name)


@roles('web')
@task
def init():
    user = env.user
    with settings(user='root', password=env.sudo_password):
        build()
        create_user(user)


@roles('web')
@task
def create_env():
    run('mkdir -p /home/%s/.ssh' % env.user)
    rsa = '/home/%s/.ssh/id_rsa_%s' % (env.user, env.project)
    xput('files/id_rsa', rsa)
    run('chmod 600 %s' % rsa)
    append('~/.ssh/config', 'IdentityFile %s' % rsa)

    profile = '~/.bash_profile_%s' % env.project
    xput('files/bash_profile', profile)
    append('~/.bashrc', 'source %s' % profile)

    run('mkdir -p ~/.pip')
    xput('files/pip.conf', '~/.pip/pip.conf')
    cmd = 'source /usr/local/bin/virtualenvwrapper.sh && mkvirtualenv %s'
    run(cmd % env.project)

    for path in [env.path, env.src, env.dist]:
        run('mkdir -p %s' % path)

    dirnames = ['data', 'etc/config', 'etc/uwsgi', 'run', 'logs']
    for dirname in dirnames:
        run('mkdir -p %s/%s' % (env.path, dirname))

    config = '%s/etc/config' % env.path
    uwsgi = '%s/etc/uwsgi' % env.path
    xput('etc/base.py', config)
    for app in env.apps:
        xput('etc/%s.py' % app, config)
        xput('uwsgi/%s.ini' % app, uwsgi)
        xput('uwsgi/%s.back.ini' % app, uwsgi)


def clone(folder, repo=None, branch=None):
    if exists(folder + '/.git'):
        run('cd %s && git stash && git pull' % folder)
    else:
        run('git clone %s %s' % (repo or env.repo, folder))

    if branch:
        run('cd %s && git checkout %s' % (folder, branch))


def clone2setup(folder, repo=None, branch=None, copy=False, install=True):
    clone(folder, repo, branch)

    requirements = os.path.join(folder, 'requirements.txt')
    if exists(requirements) and install:
        xrun('pip install -r %s' % requirements)

    with cd(folder):
        xrun('python setup.py install')

    if copy:
        for name in ['media', 'data']:
            source = os.path.join(folder, name)
            target = os.path.join(env.path, name)
            run('mkdir -p %s && cp -r %s/* %s' % (target, source, target))


def clone4github():
    repos = {
        'chiki': {
            'repo': 'https://github.com/endsh/chiki.git',
            'branch': 'old',
        },
        'simi': 'git@gitlab.com:xiaoku/simi.git',
        'flask-admin': "https://github.com/flask-admin/flask-admin.git",
    }
    for name, repo in repos.iteritems():
        folder = os.path.join(env.src, name)
        if type(repo) == dict:
            clone2setup(folder, repo['repo'], repo['branch'])
        else:
            clone2setup(folder, repo)


@roles('web')
@task
def update(install=False):
    clone2setup(os.path.join(env.src, env.project), copy=True, install=install)


@roles('web')
@task
def deploy():
    clone2setup(os.path.join(env.src, env.project), copy=True)
    clone4github()


@task
def commit(msg='auto commit'):
    local('git add --all ..')
    local('git commit -m "%s"' % msg)
    local('git push -u origin master')


@task
def sync(msg='auto commit'):
    commit(msg)
    execute(update)


@task
def up(msg='auto commit'):
    sync(msg)
    execute(restart)


@task
def upx(msg='auto commit'):
    sync(msg)
    execute(restart)
    execute(restart_back)

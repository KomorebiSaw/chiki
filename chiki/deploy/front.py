# coding: utf-8
from fabric.api import env, local, task, roles, run


@task
@roles('media')
def media(source='media/web/dist', target=None):
    target = target or env.project
    run('mkdir -p /var/htdocs/www/%s' % target)
    local(r"""

expect -c "
spawn scp -r %s/* %s@%s:/var/htdocs/www/%s
expect {
    \"*assword\" {set timeout 500; send \"%s\r\";}
    \"yes/no\" {send \"yes\r\"; exp_continue;}
}
expect eof"

        """ % (source, env.user, env.host, target, env.password))

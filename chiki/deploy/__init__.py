# coding: utf-8
from fabric.api import env, task


def set_roledefs(defs):
    for key, hosts in defs.iteritems():
        if key not in env.roledefs:
            env.roledefs[key] = []
        if type(hosts) == list:
            env.roledefs[key].extend(hosts)
        else:
            env.roledefs[key].append(hosts)

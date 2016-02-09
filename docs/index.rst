
Chiki - 基于Flask的应用层框架
=================================

Chiki是一个基于Flask的应用层框架。框架主要采用Flask扩展的设计方式，即单个模块
可用也可不用。目前主要包含了后台管理(flask-amdin)的一些扩展，接口(flask-restful)
的一些扩展，还有wtforms,mongoengine,jinja2等的一些扩展，还有短信、文件上传、
验证码、静态文件、IP处理、日志等的一些封装，以及内置通用模块、用户模块、第三方登录
集成、微信公众平台等相关支持。

Chiki相关的还有一个项目模版 `CookieCutter Chiki`_ 。使用该模版生成项目，即可直接
支持自动化部署(nginx+uwsgi+fabric)、gitlab项目同步、服务器简单管理、前端优化
(grunt+bower)。


.. _CookieCutter Chiki: https://github.com/endsh/cookiecutter-chiki

.. include:: contents.rst.inc

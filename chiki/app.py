# coding: utf-8
from flask import Flask, current_app, Response, render_template
from flask import abort, request
from flask.ext.babelex import Babel
from .jinja import init_jinja
from .logger import init_logger as _init_logger

__all__ = [
	"init_app", "init_admin",
]


def init_babel(app):
	""" 初始化语言本地化 """

	babel = Babel(app)

	@babel.localeselector
	def get_locale():
		return 'zh_Hans_CN'


def init_logger(app):
	""" 初始化日志功能 """

	if not app.debug:
		_init_logger(app)


def init_error_handler(app):
	""" 错误处理 """

	@app.errorhandler(403)
	def error_403(error):
		return render_template('403.html'), 403

	@app.errorhandler(404)
	def error_404(error):
		return render_template('404.html'), 404

	@app.errorhandler(500)
	def error_500(error):
		return render_template('500.html'), 500


def before_request():
	""" Admin 权限验证 """

	if not request.path.startswith('/admin') \
			and not request.path.startswith('/uploads') \
			and not request.path.startswith('/static'):
		return abort(403)

	auth = request.authorization
	if not (auth and auth.username == current_app.config['USERNAME'] \
			and auth.password == current_app.config['PASSWORD']):
		return Response(u'请登陆', 401, {'WWW-Authenticate': 'Basic realm="login"'})


def init_app(init, config=None, template_folder='templates'):
	""" 创建应用 """

	app = Flask(__name__, template_folder=template_folder)
	if config:
		app.config.from_object(config)

	app.static_folder = app.config.get('STATIC_FOLDER')
		
	init(app)
	init_babel(app)
	init_jinja(app)
	init_logger(app)
	init_error_handler(app)
	return app


def init_admin(init, config=None, template_folder='templates'):
	""" 创建后台管理应用 """

	app = init_app(init, config, template_folder)

	@app.before_request
	def _before_request():
		return before_request()

	return app
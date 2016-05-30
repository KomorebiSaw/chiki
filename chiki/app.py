# coding: utf-8
import os
import redis
import traceback
from flask import Blueprint, current_app, Response, render_template
from flask import abort, request, redirect
from flask.ext.babelex import Babel
from flask.ext.login import login_required
from flask.ext.mail import Mail
from flask.ext.debugtoolbar import DebugToolbarExtension
from .base import db
from .contrib.common import Item, Page, Choices, Menu
from .jinja import init_jinja
from .logger import init_logger
from .media import MediaManager
from .oauth import init_oauth
from .settings import TEMPLATE_ROOT
from .upimg import init_upimg
from ._flask import Flask

__all__ = [
    "init_app", 'init_web', 'init_api', "init_admin", "start_error",
]

DEBUG_TB_PANELS = (
    'flask_debugtoolbar.panels.versions.VersionDebugPanel',
    'flask_debugtoolbar.panels.timer.TimerDebugPanel',
    'flask_debugtoolbar.panels.headers.HeaderDebugPanel',
    'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
    'flask_debugtoolbar.panels.config_vars.ConfigVarsDebugPanel',
    'flask_debugtoolbar.panels.template.TemplateDebugPanel',
    'flask_debugtoolbar.panels.logger.LoggingPanel',
    'flask_debugtoolbar.panels.route_list.RouteListDebugPanel',
    'flask_debugtoolbar.panels.profiler.ProfilerDebugPanel',
    'flask_debugtoolbar_lineprofilerpanel.panels.LineProfilerPanel',
    'chiki.debug_toolbar_mongo.panel.MongoDebugPanel',
)

media = MediaManager()


def init_page(app):

    if app.config.get('PAGE_LOGIN_REQUIRED'):
        @app.route('/page/<int:id>.html')
        @login_required
        def page(id):
            page = Page.objects(id=id).get_or_404()
            return render_template('page.html', page=page)

        @app.route('/page/<key>.html')
        @login_required
        def page2(key):
            page = Page.objects(key=key).get_or_404()
            return render_template('page.html', page=page)

    else:
        @app.route('/page/<int:id>.html')
        def page(id):
            page = Page.objects(id=id).get_or_404()
            return render_template('page.html', page=page)

        @app.route('/page/<key>.html')
        def page2(key):
            page = Page.objects(key=key).get_or_404()
            return render_template('page.html', page=page)


def init_babel(app):
    """ 初始化语言本地化 """

    babel = Babel(app)

    @babel.localeselector
    def get_locale():
        return 'zh_Hans_CN'


def init_redis(app):
    if app.config.get('REDIS'):
        conf = app.config.get('REDIS')
        app.redis = redis.StrictRedis(
            host=conf.get('host', '127.0.0.1'),
            port=conf.get('port', 6379),
            password=conf.get('password', ''),
            db=conf.get('db', 0),
        )


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

    auth = request.authorization
    username = current_app.config.get('ADMIN_USERNAME')
    password = current_app.config.get('ADMIN_PASSWORD')
    if username and not (auth 
            and auth.username == username 
            and auth.password == password):
        return Response(u'请登陆', 401, {'WWW-Authenticate': 'Basic realm="login"'})


def init_app(init=None, config=None, pyfile=None,
        template_folder='templates', index=False, error=True,
        is_web=False, is_api=False):
    """ 创建应用 """

    app = Flask(__name__, template_folder=template_folder)
    if config: app.config.from_object(config)
    if pyfile: app.config.from_pyfile(pyfile)

    ENVVAR = app.config.get('ENVVAR')
    if ENVVAR and os.environ.get(ENVVAR):
        app.config.from_envvar(app.config['ENVVAR'])
    else:
        app.config.setdefault('DEBUG_TB_ENABLED', True)
        app.config.setdefault('DEBUG_TB_PANELS', DEBUG_TB_PANELS)
        app.config.setdefault('DEBUG_TB_INTERCEPT_REDIRECTS', False)

    toolbar = DebugToolbarExtension(app)

    app.is_web = is_web
    app.is_api = is_api
    app.static_folder = app.config.get('STATIC_FOLDER')
    app.mail = Mail(app)

    def get_data_path(name):
        return os.path.abspath(os.path.join(app.config.get('DATA_FOLDER'), name))

    app.get_data_path = get_data_path

    init_babel(app)
    init_redis(app)
    init_jinja(app)
    init_logger(app)
    init_oauth(app)
    init_page(app)
    db.init_app(app)
    media.init_app(app)

    @app.context_processor
    def context_processor():
        return dict(Item=Item, Menu=Menu)

    if error:
        init_error_handler(app)

    if callable(init):
        init(app)

    with app.app_context():
        Choices.init()

    if index:
        @app.route('/')
        def index():
            return redirect(app.config.get('INDEX_REDIRECT'))

    blueprint = Blueprint('chiki', __name__,
        template_folder=os.path.join(TEMPLATE_ROOT, 'chiki'))
    app.register_blueprint(blueprint)

    if os.environ.get('CHIKI_BACK') == 'true':
        @app.route('/chiki_back')
        def chiki_back():
            return 'true'

    return app


def init_web(init=None, config=None, pyfile=None,
        template_folder='templates', index=False, error=True):
    app = init_app(init, config, pyfile, template_folder, index, error, is_web=True)
    return app


def init_api(init=None, config=None, pyfile=None, 
        template_folder='templates', index=False, error=False):
    app = init_app(init, config, pyfile, template_folder, index, error, is_api=True)
    return app


def init_admin(init=None, config=None, pyfile=None, 
        template_folder='templates', index=True, error=True):
    """ 创建后台管理应用 """

    app = init_app(init, config, pyfile, template_folder, index, error)

    init_upimg(app)

    @app.before_request
    def _before_request():
        return before_request()

    return app


def start_error(init=None, config=None):
    app = init_app(config=config)
    app.logger.error(traceback.format_exc())
    exit()

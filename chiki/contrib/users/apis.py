# coding: utf-8
from chiki import get_ip, get_spm, get_channel, condom
from chiki.api import success, Resource
from chiki.api.const import *
from chiki.base import db
from chiki.contrib.users.base import user_manager as um
from datetime import datetime
from flask import current_app, request
from flask.ext.login import current_user, login_required
from flask.ext.login import login_user, logout_user
from werkzeug.datastructures import FileStorage

__all__ = [
    'auth_phone_code', 'auth_email_code', 'validate_email_code',
    'validate_email_code', 'userinfo', 'login',
    'SendPhoneCode', 'SendEmailCode',
    'AuthPhoneCode', 'AuthEmailCode',
    'Register', 'RegisterPhone', 'RegisterEmail',
    'Login', 'Logout', 'ResetPassword',
    'RegisterPhone', 'ResetPasswordEmail',
    'Bind', 'BindPhone', 'BindEmail',
    'UserInfo', 'resources'
]

resources = {}


def resource(*args, **kwargs):
    def wrapper(cls):
        resources[cls.__name__] = (cls, args, kwargs)
        return cls
    return wrapper


def auth_phone_code(phone, code, action):
    """ 校验手机验证码 """
    if not code:
        abort(PHONE_CODE_NOT_NULL)

    PhoneCode = um.models.PhoneCode
    item = PhoneCode.objects(phone=phone, action=action).first()
    if not item:
        abort(PHONE_CODE_ERROR)
    elif item.code != code or item.error > 10:
        item.access()
        abort(PHONE_CODE_ERROR)
    elif item.timeout:
        abort(PHONE_CODE_TIMEOUT)


def auth_email_code(email, code, action):
    """ 校验邮箱验证码 """
    if not code:
        abort(EMAIL_CODE_NOT_NULL)

    EmailCode = um.models.EmailCode
    item = PhoneCode.objects(email=email, action=action).first()
    if not item:
        abort(EMAIL_CODE_ERROR)
    elif item.code != code or item.error > 10:
        item.access()
        abort(EMAIL_CODE_ERROR)
    elif item.timeout:
        abort(EMAIL_CODE_TIMEOUT)


def validate_email_code(args, action):
    if not args['email']:
        abort(EMAIL_NOT_NULL)
    if not args['password']:
        abort(PASSWORD_NOT_NULL)
    if not args['authcode']:
        abort(EMAIL_CODE_NOT_NULL)
    if not re.match(u'[^\._-][\w\.-]+@(?:[A-Za-z0-9]+\.)+[A-Za-z]+$', args['email']):
        abort(EMAIL_FORMAT_ERROR)
    if len(args['password']) < 6 or len(args['password']) > 18:
        abort(PASSWORD_LENGTH_LIMIT)
    um.funcs.auth_email_code(args['email'], args['authcode'], action)


def validate_phone_code(args, action):
    if not args['phone']:
        abort(PHONE_NOT_NULL)
    if not args['password']:
        abort(PASSWORD_NOT_NULL)
    if not args['authcode']:
        abort(PHONE_CODE_NOT_NULL)
    if not re.match(u'^1[3578]\d{9}$|^147\d{8}$', args['phone']):
        abort(PHONE_FORMAT_ERROR)
    if len(args['password']) < 6 or len(args['password']) > 18:
        abort(PASSWORD_LENGTH_LIMIT)
    um.funcs.auth_phone_code(args['phone'], args['authcode'], action)


def userinfo(user):
    info = dict(
        id=user.id,
        phone='%s****%s' % (user.phone[:3], user.phone[7:]),
        email=user.email or '',
        nickname=user.nickname or '',
        avatar=user.avatar.get_link(64, 64),
        avatar_large=user.avatar.link,
        birthday=user.birthday.strftime('%Y-%m-%d') if user.birthday else '',
        sex=user.sex,
        location=user.location or '',
        address=user.address or '',
        debug=user.debug,
        registered=str(user.registered).split('.')[0],
    )
    return info


def login(user, device='', key=''):
    login_user(user, remember=True)
    user.login()
    um.models.UserLog.login(user.id, device, key)
    return success(**um.funcs.userinfo(user))


@resource('/users/sendcode/phone', _web=True)
class SendPhoneCode(Resource):
    """ 发送手机验证码 """

    def add_args(self):
        super(SendPhoneCode, self).add_args()
        self.req.add_argument('phone', type=unicode, required=True)

    @condom('send_phone_code')
    def post(self):
        action = request.args.get('action')
        args = self.get_args()
        self.validate(action, args)

        PhoneCode = um.models.PhoneCode
        code = PhoneCode.objects(phone=args['phone'], action=action).first()
        if code:
            if code.timelimit:
                abort(PHONE_CODE_TIME_LIMIT)
        else:
            code = PhoneCode(phone=args['phone'], action=action)

        if code.action in PhoneCode.REGISTERED_ACTIONS and code.registered:
            abort(PHONE_REGISTERED)
        elif code.action in PhoneCode.UNREGISTERED_ACTIONS and not code.registered:
            abort(PHONE_UNREGISTERED)

        condom.heart('send_phone_code')

        code.make()
        code.save()
        code.send()

        return success()

    def validate(self, action, args):
        PhoneCode = um.models.PhoneCode
        if action not in PhoneCode.ACTION_VALUES:
            abort(ACCESS_DENIED)
        if not re.match(u'^1[3578]\d{9}$|^147\d{8}$', args['phone']):
            abort(PHONE_FORMAT_ERROR)


@resource('/users/sendcode/email', _web=True)
class SendEmailCode(Resource):
    """ 发送邮箱验证码 """

    def add_args(self):
        super(SendEmailCode, self).add_args()
        self.req.add_argument('email', type=unicode, required=True)

    @condom('send_email_code')
    def post(self):
        action = request.args.get('action')
        args = self.get_args()
        self.validate(action, args)

        EmailCode = um.models.EmailCode
        code = EmailCode.objects(email=args['email'], action=action).first()
        if code:
            if code.timelimit:
                abort(EMAIL_CODE_TIME_LIMIT)
        else:
            code = EmailCode(email=args['email'], action=action)

        if code.action in EmailCode.REGISTERED_ACTIONS and code.registered:
            abort(EMAIL_REGISTERED)
        elif code.action in EmailCode.UNREGISTERED_ACTIONS and not code.registered:
            abort(EMAIL_UNREGISTERED)

        condom.heart('send_email_code')

        code.make()
        code.save()
        code.send()

        return success()

    def validate(self, action, args):
        PhoneCode = um.models.PhoneCode
        if action not in PhoneCode.ACTION_VALUES:
            abort(ACCESS_DENIED)
        if not re.match(u'[^\._-][\w\.-]+@(?:[A-Za-z0-9]+\.)+[A-Za-z]+$', args['email']):
            abort(EMAIL_FORMAT_ERROR)


class AuthCode(Resource):
    """ 校验验证码 """

    def add_args(self):
        super(AuthCode, self).add_args()
        self.req.add_argument('authcode', type=unicode, required=True)

    def post(self):
        action = request.args.get('action')
        args = self.get_args()
        self.validate(action, args)
        return success()

    def validate(self, action, args):
        raise NotImplementedError


@resource('/users/authcode/phone', _web=True)
class AuthPhoneCode(AuthCode):
    """ 校验手机验证码 """

    def add_args(self):
        super(AuthPhoneCode, self).add_args()
        self.req.add_argument('phone', type=unicode, required=True)

    def validate(self, action, args):
        if action not in um.models.PhoneCode.ACTION_VALUES:
            abort(ACCESS_DENIED)
        if not re.match(u'^1[3578]\d{9}$|^147\d{8}$', args['phone']):
            abort(PHONE_FORMAT_ERROR)
        auth_phone_code(args['phone'], args['authcode'], action)


@resource('/users/authcode/email', _web=True)
class AuthEmailCode(AuthCode):
    """ 校验邮箱验证码 """

    def add_args(self):
        super(AuthEmailCode, self).add_args()
        self.req.add_argument('email', type=unicode, required=True)

    def validate(self, action, args):
        if action not in um.models.EmailCode.ACTION_VALUES:
            abort(ACCESS_DENIED)
        if not re.match(u'[^\._-][\w\.-]+@(?:[A-Za-z0-9]+\.)+[A-Za-z]+$', args['email']):
            abort(EMAIL_FORMAT_ERROR)
        auth_email_code(args['email'], args['authcode'], action)


class Register(Resource):
    """ 用户注册 """

    key = 'unknown'

    def add_args(self):
        super(Register, self).add_args()
        self.req.add_argument('password', type=unicode, required=True)
        self.req.add_argument('authcode', type=unicode, required=True)
        self.req.add_argument('device', type=unicode, default='')
        self.not_strips = ('password', )

    def post(self):
        args = self.get_args()
        self.validate(args)
        user = self.create(args)
        um.models.UserLog.register(user.id, args['device'], key=self.key)
        return self.success(user, args)

    def create(self, args):
        raise NotImplemented

    def success(self, user, args):
        if um.config.get('register_auto_login'):
            return um.funcs.login(user, device=args['device'], key=self.key)
        return success()

    def validate(self, args):
        raise NotImplemented


@resource('/users/register/phone')
class RegisterPhone(Register):
    """ 手机注册 """

    key = 'phone'

    def add_args(self):
        super(RegisterPhone, self).add_args()
        self.req.add_argument('phone', type=unicode, required=True)

    def create(self, args):
        user = um.models.User(
            phone=args['phone'],
            password=args['password'],
            channel=get_channel(),
            spm=get_spm(),
            ip=get_ip(),
        )
        user.create()
        return user

    def validate(self, args):
        validate_phone_code(args, um.models.PhoneCode.ACTION_REGISTER)
        if um.models.User.objects(phone=args['phone']).count() > 0:
            abort(PHONE_EXISTS)


@resource('/users/register/email')
class RegisterEmail(Register):
    """ 邮箱注册 """

    key = 'email'

    def add_args(self):
        super(RegisterEmail, self).add_args()
        self.req.add_argument('email', type=unicode, required=True)

    def create(self, args):
        user = um.models.User(
            email=args['email'],
            password=args['password'],
            channel=get_channel(),
            spm=get_spm(),
            ip=get_ip(),
        )
        user.create()
        return user

    def validate(self, args):
        validate_phone_code(args, um.models.EmailCode.ACTION_REGISTER)
        if um.models.User.objects(email=args['email']).count() > 0:
            abort(EMAIL_EXISTS)


@resource('/users/login')
class Login(Resource):
    """ 用户登录 """

    def add_args(self):
        super(Login, self).add_args()
        self.req.add_argument('account', type=unicode, required=True)
        self.req.add_argument('password', type=unicode, required=True)
        self.req.add_argument('device', type=unicode, default='')
        self.not_strips = ('password', )

    def get(self):
        abort(LOGIN_REQUIRED)

    def post(self):
        args = self.get_args()
        self.validate(args)

        doc = db.Q(phone=args['account']) | db.Q(email=args['account'])
        user = um.models.User.objects(doc).first()
        if not user:
            abort(ACCCOUNT_NOT_EXISTS)
        if user.is_lock:
            abort(ACCOUNT_LOCKED)
        if user.password != args['password']:
            user.login_error()
            abort(PASSWORD_ERROR)

        return self.success(user, args)

    def success(self, user, args):
        key = 'phone' if user.phone == args['account'] else 'email'
        return um.funcs.login(user, device=args['device'], key=key)

    def validate(self, args):
        if not args['account']:
            abort(ACCOUNT_NOT_NULL)
        if not args['password']:
            abort(PASSWORD_NOT_NULL)


@resource('/users/logout')
class Logout(Resource):
    """ 用户退出 """

    def add_args(self):
        super(Logout, self).add_args()
        self.req.add_argument('device', type=unicode, default='')

    def post(self):
        args = self.get_args()
        if current_user.is_authenticated():
            um.models.UserLog.logout(current_user.id, args['device'])

        logout_user()
        return success()


class ResetPassword(Resource):
    """ 重置密码 """

    key = 'unknown'

    def add_args(self):
        super(ResetPassword, self).add_args()
        self.req.add_argument('password', type=unicode, required=True)
        self.req.add_argument('authcode', type=unicode, required=True)
        self.req.add_argument('device', type=unicode, default='')
        self.not_strips = ('password', )

    def post(self):
        args = self.get_args()
        self.validate(args)
        user = self.get_user(args)
        if not user:
            abort(ACCOUNT_NOT_EXISTS)

        user.reset_password(args['password'])
        um.models.UserLog.reset_password(user.id, args['device'], key=self.key)

        logout_user()
        return self.success(user, args)

    def success(self, user, args):
        if um.config.get('reset_password_auto_login'):
            return um.funcs.login(user, device=args['device'], key=self.key)
        return success()

    def get_user(self):
        raise NotImplementedError

    def validate(self, args):
        raise NotImplementedError


@resource('/users/reset_password/phone')
class ResetPasswordPhone(Resource):
    """ 手机重置密码 """

    key = 'phone'

    def add_args(self):
        super(ResetPasswordPhone, self).add_args()
        self.req.add_argument('phone', type=unicode, required=True)

    def get_user(self, args):
        return um.models.User.objects(phone=args['phone']).first()

    def validate(self, args):
        validate_phone_code(args, um.models.PhoneCode.ACTION_RESET_PASSWORD)


@resource('/users/reset_password/email')
class ResetPasswordEmail(Resource):
    """ 邮箱重置密码 """

    key = 'email'

    def add_args(self):
        super(ResetPasswordEmail, self).add_args()
        self.req.add_argument('email', type=unicode, required=True)

    def get_user(self, args):
        return um.models.User.objects(email=args['email']).first()

    def validate(self, args):
        validate_email_code(args, um.models.EmailCode.ACTION_RESET_PASSWORD)


class Bind(Resource):
    """ 绑定 """

    key = 'unknown'

    def add_args(self):
        super(Bind, self).add_args()
        self.req.add_argument('password', type=unicode, required=True)
        self.req.add_argument('authcode', type=unicode, required=True)
        self.req.add_argument('device', type=unicode, default='')
        self.not_strips = ('password', )

    @login_required
    def post(self):
        if current_user.is_user:
            abort(NOT_ALLOW_BIND)

        args = self.get_args()
        self.validate(args)
        user = self.bind(args)

        current_user.user = user.id
        current_user.save()

        um.models.UserLog.bind(user.id, args['device'], key=self.key)
        return self.success(user, args)

    def create(self, args):
        raise NotImplemented

    def success(self, user, args):
        return um.funcs.login(user, device=args['device'], key=self.key)

    def validate(self, args):
        raise NotImplemented


@resource('/u/bind/phone')
class BindPhone(Resource):
    """ 绑定手机 """

    key = 'phone'

    def add_args(self):
        super(BindPhone, self).add_args()
        self.req.add_argument('phone', type=unicode, required=True)

    def bind(self, args):
        user = um.models.User.objects(phone=args['phone']).first()
        if not user:
            user = um.models.User(
                phone=args['phone'],
                password=args['password'],
                channel=get_channel(),
                spm=get_spm(),
                ip=get_ip(),
            )
            user.create()
        elif user.password != args['password']:
            abort(PASSWORD_ERROR)
        return user

    def validate(self, args):
        validate_phone_code(args, um.models.PhoneCode.ACTION_BIND)


@resource('/u/bind/email')
class BindEmail(Resource):
    """ 绑定邮箱 """

    key = 'email'

    def add_args(self):
        super(BindEmail, self).add_args()
        self.req.add_argument('email', type=unicode, required=True)

    def bind(self, args):
        user = um.models.User.objects(email=args['email']).first()
        if not user:
            user = um.models.User(
                email=args['email'],
                password=args['password'],
                channel=get_channel(),
                spm=get_spm(),
                ip=get_ip(),
            )
            user.create()
        elif user.password != args['password']:
            abort(PASSWORD_ERROR)
        return user

    def validate(self, args):
        validate_email_code(args, um.models.EmailCode.ACTION_BIND)


@resource('/u')
class UserInfo(Resource):
    """ 用户信息 """

    def add_args(self):
        super(UserInfo, self).add_args()
        self.req.add_argument('nickname', type=unicode)
        self.req.add_argument('avatar', type=FileStorage, location='files')
        self.req.add_argument('birthday', type=unicode)
        self.req.add_argument('sex', type=unicode)
        self.req.add_argument('location', type=unicode)
        self.req.add_argument('address', type=unicode)

    @login_required
    def get(self):
        return success(**um.funcs.userinfo(current_user))

    @login_required
    def post(self):
        if not current_user.is_user:
            abort(NEED_BIND)

        args = get_args()
        self.handle(args)
        current_user.save()

        return success(**userinfo(current_user))

    def handles(self, args):
        self.handle(args, 'nickname')
        self.handle(args, 'avatar')
        self.handle(args, 'birthday')
        self.handle(args, 'sex')
        self.handle(args, 'location')
        self.handle(args, 'address')

    def handle(self, args, key):
        if key in args and args[key]:
            getattr(self, 'handle_%s' % key)(args[key])

    def handle_nickname(self, nickname):
        unique = current_app.config.get('NICKNAME_UNIQUE')
        if unique and nickname != current_user.nickname \
                and um.models.User.objects(nickname=nickname).count() > 0:
            abort(USER_NICKNAME_EXISTS)
        current_user.nickname = nickname

    def handle_avatar(self, avatar):
        format = avatar.filename.split('.')[-1]
        User = um.models.User
        if User.avatar.allows and format not in User.avatar.allows:
            abort(FILE_FORMAT_NOT_SUPPORT)
        if User.avatar.max_size and avatar.content_length > User.avatar.max_size:
            abort(FILE_SIZE_LIMIT)
        if not is_empty(avatar.stream):
            current_user.avatar = avatar

    def handle_birthday(self, birthday):
        try:
            current_user.birthday = datetime.strptime(birthday, '%Y-%m-%d')
        except:
            pass

    def handle_sex(self, sex):
        if sex not in User.SEX_VALUES:
            abort(USER_SEX_ERROR)
        current_user.sex = sex

    def handle_location(self, location):
        current_user.location = location

    def handle_address(self, address):
        current_user.address = address

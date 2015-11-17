# coding: utf-8
from chiki import strip, get_ip, get_spm, get_channel, condom
from chiki.api import success
from chiki.api.const import *
from chiki.base import db
from chiki.contrib.users.base import user_manager as um
from flask import current_app, request
from flask.ext.login import current_user, login_required
from flask.ext.login import login_user, logout_user
from flask.ext.restful import Resource as _Resource, reqparse


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
    auth_email_code(args['email'], args['authcode'], action)


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
    auth_phone_code(args['phone'], args['authcode'], action)


class Resource(_Resource):

    def __init__(self):
        super(Resource, self).__init__()
        self.req = reqparse.RequestParser()
        self.add_args()

    def add_args():
        



class SendPhoneCode(Resource):
    """ 发送手机验证码 """

    def __init__(self):
        super(SendPhoneCode, self).__init__()
        self.req = reqparse.RequestParser()
        self.req.add_argument('phone', type=unicode, required=True)

    @condom('send_phone_code')
    def post(self):
        action = request.args.get('action')
        args = strip(self.req.parse_args())
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


class SendEmailCode(Resource):
    """ 发送邮箱验证码 """

    def __init__(self):
        super(SendEmailCode, self).__init__()
        self.req = reqparse.RequestParser()
        self.req.add_argument('email', type=unicode, required=True)

    @condom('send_email_code')
    def post(self):
        action = request.args.get('action')
        args = strip(self.req.parse_args())
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

    def __init__(self):
        super(AuthCode, self).__init__()
        self.req = reqparse.RequestParser()
        self.req.add_argument('authcode', type=unicode, required=True)

    def post(self):
        action = request.args.get('action')
        args = strip(self.req.parse_args())
        self.validate(action, args)
        return success()

    def validate(self, action, args):
        raise NotImplementedError


class AuthPhoneCode(AuthCode):
    """ 校验手机验证码 """

    def __init__(self):
        super(AuthPhoneCode, self).__init__()
        self.req.add_argument('phone', type=unicode, required=True)

    def validate(self, action, args):
        if action not in um.models.PhoneCode.ACTION_VALUES:
            abort(ACCESS_DENIED)
        if not re.match(u'^1[3578]\d{9}$|^147\d{8}$', args['phone']):
            abort(PHONE_FORMAT_ERROR)
        auth_phone_code(args['phone'], args['authcode'], action)


class AuthEmailCode(AuthCode):
    """ 校验邮箱验证码 """

    def __init__(self):
        super(AuthEmailCode, self).__init__()
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

    def __init__(self):
        super(Register, self).__init__()
        self.req = reqparse.RequestParser()
        self.req.add_argument('password', type=unicode, required=True)
        self.req.add_argument('authcode', type=unicode, required=True)
        self.req.add_argument('device', type=unicode, default='')

    def post(self):
        args = strip(self.req.parse_args(), 'password')
        self.validate(args)
        user = self.create(args)
        um.models.UserLog.register(user.id, args['device'], key=self.key)
        return self.success(user, args)

    def create(self, args):
        raise NotImplemented

    def success(self, user, args):
        if um.config.get('register_auto_login'):
            return login(user, device=args['device'], key=self.key)
        return success()

    def validate(self, args):
        raise NotImplemented


class RegisterEmail(Register):
    """ 邮箱注册 """

    key = 'email'

    def __init__(self):
        super(RegisterEmail, self).__init__()
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


class RegisterPhone(Register):
    """ 手机注册 """

    key = 'phone'

    def __init__(self):
        super(RegisterPhone, self).__init__()
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


class Login(Resource):
    """ 用户登录 """

    def __init__(self):
        super(Login, self).__init__()
        self.req = reqparse.RequestParser()
        self.req.add_argument('account', type=unicode, required=True)
        self.req.add_argument('password', type=unicode, required=True)
        self.req.add_argument('device', type=unicode, default='')

    def get(self):
        abort(LOGIN_REQUIRED)

    def post(self):
        args = strip(self.req.parse_args(), 'password')
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
        return login(user, device=args['device'], key=key)

    def validate(self, args):
        if not args['account']:
            abort(ACCOUNT_NOT_NULL)
        if not args['password']:
            abort(PASSWORD_NOT_NULL)


class Logout(Resource):
    """ 用户退出 """

    def __init__(self):
        super(Logout, self).__init__()
        self.req = reqparse.RequestParser()
        self.req.add_argument('device', type=unicode, default='')

    def post(self):
        args = strip(self.req.parse_args())
        if current_user.is_authenticated():
            um.models.UserLog.logout(current_user.id, args['device'])

        logout_user()
        return success()


class ResetPassword(Resource):
    """ 重置密码 """

    key = 'unknown'

    def __init__(self):
        super(ResetPassword, self).__init__()
        self.req = reqparse.RequestParser()
        self.req.add_argument('password', type=unicode, required=True)
        self.req.add_argument('authcode', type=unicode, required=True)
        self.req.add_argument('device', type=unicode, default='')

    def post(self):
        args = strip(self.req.parse_args(), 'password')
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
            return login(user, device=args['device'], key=self.key)
        return success()

    def get_user(self):
        raise NotImplementedError

    def validate(self, args):
        raise NotImplementedError


class ResetPasswordEmail(Resource):
    """ 邮箱重置密码 """

    key = 'email'

    def __init__(self):
        super(ResetPasswordEmail, self).__init__()
        self.req.add_argument('email', type=unicode, required=True)

    def get_user(self, args):
        return um.models.User.objects(email=args['email']).first()

    def validate(self, args):
        validate_email_code(args, um.models.EmailCode.ACTION_RESET_PASSWORD)


class ResetPasswordPhone(Resource):
    """ 手机重置密码 """

    key = 'phone'

    def __init__(self):
        super(ResetPasswordPhone, self).__init__()
        self.req.add_argument('phone', type=unicode, required=True)

    def get_user(self, args):
        return um.models.User.objects(phone=args['phone']).first()

    def validate(self, args):
        validate_phone_code(args, um.models.PhoneCode.ACTION_RESET_PASSWORD)


class Bind(Resource):
    """ 绑定 """

    key = 'unknown'

     def __init__(self):
        super(Bind, self).__init__()
        self.req = reqparse.RequestParser()
        self.req.add_argument('password', type=unicode, required=True)
        self.req.add_argument('authcode', type=unicode, required=True)
        self.req.add_argument('device', type=unicode, default='')



class BindEmail(Resource):
    """ 绑定邮箱 """

    key = 'email'


class BindPhone(Resource):
    """ 绑定手机 """

    key = 'phone'


class UserInfo(Resource):
    """ 用户信息 """

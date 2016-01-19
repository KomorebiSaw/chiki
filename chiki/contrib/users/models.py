# coding: utf-8
import hashlib
import random
from chiki import get_ip, get_spm, get_channel, url2image
from chiki.base import db
from chiki.utils import get_spm, get_ip
from chiki.contrib.common import Item
from chiki.contrib.users.base import user_manager as um
from datetime import datetime, timedelta
from flask import current_app, request
from flask.ext.login import current_user

__all__ = [
    'User', 'UserMixin', 'WeChatUser', 'QQUser', 'WeiBoUser',
    'UserLog', 'PhoneCode', 'EmailCode',
]


class UserMixin(object):

    @staticmethod
    def get_wechat(**kwargs):
        user = um.models.WeChatUser.objects(**kwargs).first()
        if user:
            return user.current or user

    @staticmethod
    def create_empty():
        return um.models.User(channel=get_channel(), spm=get_spm(), ip=get_ip())

    @staticmethod
    def from_oauth(user):
        return user.oauth()

    @staticmethod
    def from_wechat(wxuser):
        if wxuser.user:
            user = wxuser.current
            if user:
                return user

        user = um.models.User.create_empty()
        user.nickname = wxuser.nickname
        user.avatar = url2image(wxuser.headimgurl)
        user.sex = user.SEX_FROM_WECHAT.get(wxuser.sex, user.SEX_UNKNOWN)
        user.country = wxuser.country
        user.location = '%s|%s' % (wxuser.province, wxuser.city)
        user.create()
        wxuser.user = user.id
        wxuser.save()
        return user

    @staticmethod
    def from_wechat_mp(openid):
        return um.models.User.from_wechat(um.models.WeChatUser.create_mp(openid))

    @staticmethod
    def from_qq(ouser):
        pass

    @staticmethod
    def from_weibo(ouser):
        pass

    def __unicode__(self):
        return '%s - %s' % (self.phone, self.id)

    @property
    def wechat_user(self):
        return um.models.WeChatUser.objects(user=self.id).first()

    @property
    def is_lock(self):
        return self.locked > datetime.now() - timedelta(seconds=300)

    @property
    def avatar_small(self):
        return self.get_avatar(64, 64)

    @property
    def avatar_lagre(self):
        return self.get_avatar()

    def get_avatar(self, width=128, height=128):
        if self.avatar:
            return self.avatar.get_link(width, height)
        return current_app.config.get('DEFAULT_AVATAR')

    def create(self):
        """ 创建用户 """
        if not self.id:
            self.id = Item.inc('user_index', 100000)
            self.save()
        return self.id

    def login(self):
        """ 用户登录 """
        self.logined = datetime.now()
        self.ip = get_ip()
        self.spm = request.args.get('spm', self.spm)
        self.save()

    def login_error(self):
        """ 登录错误 """
        self.error += 1
        if self.error >= 10:
            self.locked = datetime.now()
            self.error = 0
        self.save()

    def reset_password(self, password):
        """ 重置密码 """
        self.locked = datetime(1970, 1, 1)
        self.error = 0
        self.password = password
        self.save()

    def is_user(self):
        return True

    def is_authenticated(self):
        """ 是否登录 """
        return True

    def is_active(self):
        """ 是否激活 """
        return self.active

    def is_anonymous(self):
        """ 是否游客 """
        return False

    def get_id(self):
        """ 获取用户ID """
        return self.id


class User(db.Document, UserMixin):
    """ 用户模型 """

    SEX_UNKNOWN = 'unknown'
    SEX_MALE = 'male'
    SEX_FEMALE = 'female'
    SEX_CHOICES = (
        (SEX_UNKNOWN, '保密'),
        (SEX_MALE, '男'),
        (SEX_FEMALE, '女'),
    )
    SEX_VALUES = [x[0] for x in SEX_CHOICES]
    SEX_FROM_WECHAT = {0: SEX_UNKNOWN, 1: SEX_MALE, 2: SEX_FEMALE}

    id = db.IntField(primary_key=True, verbose_name='ID')
    phone = db.StringField(max_length=20, verbose_name='手机')
    email = db.StringField(max_length=40, verbose_name='邮箱')
    password = db.StringField(max_length=40, verbose_name='密码')
    nickname = db.StringField(max_length=40, verbose_name='昵称')
    avatar = db.XImageField(verbose_name='头像')
    birthday = db.DateTimeField(verbose_name='生日')
    sex = db.StringField(default=SEX_UNKNOWN, choices=SEX_CHOICES, verbose_name='性别')
    location = db.AreaField(verbose_name='所在地')
    address = db.StringField(max_length=100, verbose_name='通讯地址')
    debug = db.BooleanField(default=False, verbose_name='允许调试')
    active = db.BooleanField(default=True, verbose_name='激活')
    channel = db.IntField(verbose_name='注册渠道ID')
    spm = db.StringField(max_length=100, verbose_name='登录SPM')
    ip = db.StringField(max_length=20, verbose_name='登录IP')
    generate = db.BooleanField(default=False, verbose_name='生成')
    error = db.IntField(default=0, verbose_name='登录错误次数')
    locked = db.DateTimeField(default=lambda: datetime(1970, 1, 1), verbose_name='锁定时间')
    logined = db.DateTimeField(default=lambda: datetime.now(), verbose_name='登录时间')
    registered = db.DateTimeField(default=lambda: datetime.now(), verbose_name='注册时间')

    meta = {
        'indexes': [
            'phone',
            'nickname',
            'ip',
            '-logined',
            '-registered',
        ],
    }


class ThirdUserMixin(object):

    @property
    def current(self):
        return um.models.User.objects(id=self.user).first()

    def is_user(self):
        return False

    def is_authenticated(self):
        """ 是否登录 """
        return True

    def is_active(self):
        """ 是否激活 """
        return True

    def is_anonymous(self):
        """ 是否游客 """
        return False

    def get_id(self):
        """ 获取用户ID """
        return '%s:%s' % (self.key, str(self.id))


class WeChatUser(db.Document, ThirdUserMixin):
    """ 微信用户信息 """

    key = 'wechat'

    user = db.IntField(verbose_name='用户')
    unionid = db.StringField(verbose_name='联合ID')
    mp_openid = db.StringField(verbose_name='公众号ID')
    mobile_openid = db.StringField(verbose_name='手机ID')
    qrcode_openid = db.StringField(verbose_name='二维码ID')
    nickname = db.StringField(verbose_name='昵称')
    sex = db.IntField(verbose_name='性别')
    country = db.StringField(verbose_name='国家')
    province = db.StringField(verbose_name='省份')
    city = db.StringField(verbose_name='城市')
    headimgurl = db.StringField(verbose_name='头像链接')
    privilege = db.ListField(db.StringField(), verbose_name='特权信息')
    subscribe = db.BooleanField(default=False, verbose_name='是否关注公众号')
    subscribe_time = db.DateTimeField(verbose_name='关注时间')
    remark = db.StringField(max_length=40, verbose_name='备注')
    groupid = db.IntField(default=0, verbose_name='分组ID')
    access_token = db.StringField(verbose_name='令牌')
    expires_in = db.DateTimeField(verbose_name='过期时间')
    refresh_token = db.StringField(verbose_name='令牌刷新')
    updated = db.DateTimeField(default=datetime.now, verbose_name='更新时间')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            'user',
            'unionid',
            'mp_openid',
            'mobile_openid',
            'qrcode_openid',
            '-modified',
            '-created',
        ],
    }

    def __unicode__(self):
        return 'WeChat %d - %s' % (self.user or 0, self.unionid)

    @staticmethod
    def create(userinfo, action):
        user = WeChatUser()
        if current_user.is_authenticated() and current_user.is_user():
            user.user = current_user.id

        user.update_info(userinfo, action)
        user.save()
        return user

    @staticmethod
    def create_mp(openid):
        user = WeChatUser(mp_openid=openid)
        if current_user.is_authenticated() and current_user.is_user():
            user.user = current_user.id

        user.update(True)
        user.save()
        return user

    def oauth(self):
        return um.models.User.from_wechat(self)

    def update(self, force=False):
        if force or self.updated + timedelta(days=1) < datetime.now():
            self.updated = datetime.now()
            self.update_info(current_app.wxauth.get_user_info(self.mp_openid), 'mp')
            self.save()

    def update_info(self, userinfo, action):
        setattr(self, action + '_openid', userinfo['openid'])
        self.unionid = userinfo.get('unionid', '')
        self.nickname = userinfo['nickname']
        self.sex = userinfo['sex']
        self.province = userinfo['province']
        self.city = userinfo['city']
        self.country = userinfo['country']
        self.headimgurl = userinfo['headimgurl']
        self.privilege = userinfo.get('privilege', self.privilege)
        if userinfo.get('subscribe') == 1:
            self.remark = userinfo['remark']
            self.language = userinfo['language']
            self.groupid = userinfo['groupid']
            self.subscribe = True
            self.subscribe_time = datetime.fromtimestamp(userinfo['subscribe_time'])


class QQUser(db.Document, ThirdUserMixin):
    """ QQ用户信息 """

    key = 'qq'

    user = db.IntField(verbose_name='用户')
    openid = db.StringField(verbose_name='开放ID')
    nickname = db.StringField(verbose_name='昵称')
    figureurl = db.StringField(verbose_name='空间头像')
    figureurl_1 = db.StringField(verbose_name='空间头像1')
    figureurl_2 = db.StringField(verbose_name='空间头像2')
    figureurl_qq_1 = db.StringField(verbose_name='头像链接')
    figureurl_qq_2 = db.StringField(verbose_name='头像链接2')
    is_yellow_vip = db.IntField(verbose_name='黄钻')
    vip = db.IntField(verbose_name='黄钻2')
    yellow_vip_level = db.IntField(verbose_name='黄钻等级')
    level = db.IntField(verbose_name='黄钻等级2')
    is_yellow_year_vip = db.IntField(verbose_name='年黄钻')
    access_token = db.StringField(verbose_name='令牌')
    expires_in = db.DateTimeField(verbose_name='过期时间')
    refresh_token = db.StringField(verbose_name='令牌刷新')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            'user',
            'openid',
            '-modified',
            '-created',
        ],
    }

    def __unicode__(self):
        return 'QQ %d - %s' % (self.user or 0, self.openid)

    def oauth(self):
        return um.models.User.from_qq(self)


class WeiBoUser(db.Document, ThirdUserMixin):
    """ QQ用户信息 """

    key = 'weibo'

    user = db.IntField(verbose_name='用户')
    uid = db.IntField(verbose_name='ID')
    nickname = db.StringField(verbose_name='昵称')
    sex = db.IntField(verbose_name='性别')
    country = db.StringField(verbose_name='国家')
    province = db.StringField(verbose_name='省份')
    city = db.StringField(verbose_name='城市')
    headimgurl = db.StringField(verbose_name='头像链接')
    headimgurl_large = db.StringField(verbose_name='头像链接2')
    headimgurl_hd = db.StringField(verbose_name='头像链接3')
    subscribe = db.BooleanField(default=False, verbose_name='是否关注')
    subscribe_time = db.DateTimeField(verbose_name='关注时间')
    follow = db.IntField(verbose_name='是否关注')
    access_token = db.StringField(verbose_name='令牌')
    expires_in = db.DateTimeField(verbose_name='过期时间')
    refresh_token = db.StringField(verbose_name='令牌刷新')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            'user',
            'uid',
            '-modified',
            '-created',
        ],
    }

    def __unicode__(self):
        return 'WeiBo %d - %d' % (self.user or 0, self.uid)

    def oauth(self):
        return um.models.User.from_weibo(self)


class UserLog(db.Document):
    """ 用户日志 """

    TYPE_BIND = 'bind'
    TYPE_REGISTER = 'register'
    TYPE_LOGIN = 'login'
    TYPE_LOGOUT = 'logout'
    TYPE_CHANGE_PASSWORD = 'change_password'
    TYPE_RESET_PASSWORD = 'reset_password'
    TYPE_CHOICES = (
        (TYPE_BIND, '绑定手机'),
        (TYPE_REGISTER, '注册'),
        (TYPE_LOGIN, '登录'),
        (TYPE_LOGOUT, '退出'),
        (TYPE_CHANGE_PASSWORD, '修改密码'),
        (TYPE_RESET_PASSWORD, '重置密码'),
    )
    TYPE_VALUES = [x[0] for x in TYPE_CHOICES]

    user = db.IntField(verbose_name='用户')
    type = db.StringField(choices=TYPE_CHOICES, verbose_name='类型')
    key = db.StringField(verbose_name='键')
    device = db.StringField(max_length=100, verbose_name='设备ID')
    spm = db.StringField(max_length=100, verbose_name='SPM')
    ip = db.StringField(max_length=20, verbose_name='IP')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            'user',
            'ip',
            '-created',
        ],
    }

    def __unicode__(self):
        return '%d - %s' % (self.user, self.type)

    @staticmethod
    def log(type, id, device, key='', spm=None, ip=None):
        spm = spm if spm else get_spm()
        ip = ip if ip else get_ip()
        UserLog(user=id, type=type, device=device, key=key, spm=spm, ip=ip).save()

    @staticmethod
    def bind(id, device, key='', spm=None, ip=None):
        UserLog.log(UserLog.TYPE_BIND, id, device, key, spm, ip)

    @staticmethod
    def register(id, device, key='', spm=None, ip=None):
        UserLog.log(UserLog.TYPE_REGISTER, id, device, key, spm, ip)

    @staticmethod
    def login(id, device, key='', spm=None, ip=None):
        UserLog.log(UserLog.TYPE_LOGIN, id, device, key, spm, ip)

    @staticmethod
    def logout(id, device, key='', spm=None, ip=None):
        UserLog.log(UserLog.TYPE_LOGOUT, id, device, key, spm, ip)

    @staticmethod
    def change_password(id, device, key='', spm=None, ip=None):
        UserLog.log(UserLog.TYPE_CHNAGE_PASSWORD, id, device, key, spm, ip)

    @staticmethod
    def reset_password(id, device, key='', spm=None, ip=None):
        UserLog.log(UserLog.TYPE_RESET_PASSWORD, id, device, key, spm, ip)


class PhoneCode(db.Document):
    """ 手机验证码 """

    ACTION_BIND = 'bind'
    ACTION_REGISTER = 'register'
    ACTION_RESET_PASSWORD = 'reset_password'
    ACTION_CHOICES = (
        (ACTION_BIND, '绑定'),
        (ACTION_REGISTER, '注册'),
        (ACTION_RESET_PASSWORD, '重置密码'),
    )
    ACTION_VALUES = [x[0] for x in ACTION_CHOICES]
    REGISTERED_ACTIONS = (ACTION_REGISTER,)
    UNREGISTERED_ACTIONS = (ACTION_RESET_PASSWORD,)

    phone = db.StringField(max_length=20, verbose_name='手机')
    action = db.StringField(choices=ACTION_CHOICES, verbose_name='类型')
    code = db.StringField(max_length=40, verbose_name='验证码')
    error = db.IntField(default=0, verbose_name='错误次数')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            ('phone', 'action'),
            '-created',
        ],
    }

    def __unicode__(self):
        return '<%s - %s>' % (self.phone, self.action)

    @property
    def timelimit(self):
        return datetime.now() < self.created + timedelta(seconds=60)

    @property
    def timeout(self):
        return datetime.now() > self.created + timedelta(seconds=1800)

    @property
    def registered(self):
        User = um.models.User
        return User.objects(phone=self.phone).count() > 0

    def make(self):
        self.created = datetime.now()
        self.code = str(random.randint(1000, 9999))
        self.save()

    def send(self):
        um.funcs.send_sms(self)

    def access(self):
        self.error += 1
        self.save()


class EmailCode(db.Document):
    """ 邮箱验证码 """

    ACTION_BIND = 'bind'
    ACTION_REGISTER = 'register'
    ACTION_RESET_PASSWORD = 'reset_password'
    ACTION_CHOICES = (
        (ACTION_BIND, '绑定'),
        (ACTION_REGISTER, '注册'),
        (ACTION_RESET_PASSWORD, '重置密码'),
    )
    ACTION_VALUES = [x[0] for x in ACTION_CHOICES]
    REGISTERED_ACTIONS = (ACTION_REGISTER,)
    UNREGISTERED_ACTIONS = (ACTION_RESET_PASSWORD,)

    email = db.StringField(max_length=40, verbose_name='邮箱')
    action = db.StringField(choices=ACTION_CHOICES, verbose_name='类型')
    code = db.StringField(max_length=40, verbose_name='验证码')
    token = db.StringField(max_length=40, verbose_name='令牌')
    error = db.IntField(default=0, verbose_name='错误次数')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            ('email', 'action'),
            '-created',
        ],
    }

    def __unicode__(self):
        return '<%s - %s>' % (self.phone, self.action)

    @staticmethod
    def get(token):
        return EmailCode.objects(token=token).first()

    @property
    def timelimit(self):
        return datetime.now() < self.created + timedelta(seconds=60)

    @property
    def timeout(self):
        return datetime.now() > self.created + timedelta(seconds=1800)

    @property
    def registered(self):
        User = um.models.User
        return User.objects(email=self.email).count() > 0

    def make(self):
        self.created = datetime.now()
        self.code = str(random.randint(1000, 9999))
        self.token = hashlib.md5('%s%s%s' % (self.email, self.code, str(self.created))).hexdigest()
        self.save()

    def send(self):
        um.funcs.send_mail(self)

    def access(self):
        self.error += 1
        self.save()

#coding: utf-8
from chiki.forms import Form
from wtforms import BooleanField, PasswordField, TextField
from chiki.forms import Strip, Lower, DataRequired
from .models import AdminUser


class LoginForm(Form):
    account = TextField('用户名/邮箱/手机',
                        validators=[Strip(), Lower(), DataRequired()])
    password = PasswordField('密码', validators=[])
    remember = BooleanField('记住登录状态')

    def validate_account(self, field):
        admin = AdminUser.objects(
            username=self.account.data).first()
        if not admin:
            raise ValueError('用户不存在')
        if admin.password != self.password.data:
            raise ValueError('密码错误')

        self.admin = admin

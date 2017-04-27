#coding: utf-8
from flask import Blueprint
from flask import redirect, render_template, request, url_for
from chiki.contrib.admin.form import LoginForm
from flask.ext.login import login_user, logout_user, current_user
from datetime import datetime
from chiki.contrib.admin.models import AdminUserLoginLog

bp = Blueprint('admin_users', __name__)


@bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    next = request.args.get('next', '/admin')
    if current_user.is_authenticated():
        return redirect(next)

    form = LoginForm()
    if form.validate_on_submit():
        login_user(form.admin, remember=form.remember.data)
        current_user.logined = datetime.now()
        current_user.save()
        AdminUserLoginLog.login(current_user.id)
        return redirect(next)
    return render_template('admin/login.html', form=form)


@bp.route('/admin/logout')
def admin_logout():
    if current_user.is_authenticated():
        AdminUserLoginLog.logout(current_user.id)
        logout_user()
    return redirect(url_for('admin_users.admin_login'))

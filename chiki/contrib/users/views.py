# coding: utf-8
from flask import Blueprint, request, render_template, redirect
from flask import url_for

bp = Blueprint('users', __name__)


@bp.route('/register')
def register():
    pass


@bp.route('/login')
def login():
    pass


@bp.route('/logout')
def logout():
    pass


@bp.route('/')
def reset_password():
    pass

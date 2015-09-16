# coding: utf-8
from flask import Blueprint
from flask.ext.login import LoginManager
from .mongoengine import MongoEngine

db = MongoEngine()
login = LoginManager()
page = Blueprint('page', __name__)

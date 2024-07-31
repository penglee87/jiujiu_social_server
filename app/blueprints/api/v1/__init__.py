from flask import Blueprint

api_bl = Blueprint('api_v1', __name__)

from . import authentication, posts, users, comments, errors, wx_auth

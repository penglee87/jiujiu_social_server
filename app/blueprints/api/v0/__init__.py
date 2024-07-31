from flask import Blueprint

api_bl = Blueprint('api', __name__)

from . import authentication, posts, users, comments, errors

from flask import Blueprint

api_bl = Blueprint('api_v2', __name__)

from . import laboratory, posts, comments, users, auth, upload_file, chat

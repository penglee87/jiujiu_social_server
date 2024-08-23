from flask import Blueprint

api_bl = Blueprint('api_v2', __name__)

from . import posts, comments, users, auth, upload_file, chat, labroratory

from flask import Blueprint

auth_bl = Blueprint('auth', __name__)

from . import views

from flask import Blueprint

chat_bl = Blueprint('chat', __name__)

from . import views, errors
from app.models import Permission


@chat_bl.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)

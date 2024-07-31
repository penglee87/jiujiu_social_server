from flask import Blueprint

main_bl = Blueprint('main', __name__)

from . import views, errors
from app.models import Permission


@main_bl.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)

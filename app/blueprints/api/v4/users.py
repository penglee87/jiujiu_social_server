from flask import jsonify, request, current_app, url_for
from lib.redprint import RedPrint
from app.models import User, Post

api_rp = RedPrint('users', __name__)

@api_rp.route('/<int:id>')
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify(user.to_json())


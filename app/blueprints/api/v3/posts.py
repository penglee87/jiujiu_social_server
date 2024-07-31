from flask import jsonify, request, g, url_for, current_app
from app import db
from app.models import Post, Permission
from lib.redprint import RedPrint

api_rp = RedPrint('posts', __name__)

@api_rp.route('/')
def get_posts():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.paginate(
        page=page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for(f'{request.blueprint}.get_posts', page=page-1)
    next = None
    if pagination.has_next:
        next = url_for(f'{request.blueprint}.get_posts', page=page+1)
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api_rp.route('/<int:id>')
def get_post(id):
    post = Post.query.get_or_404(id)
    return jsonify(post.to_json())
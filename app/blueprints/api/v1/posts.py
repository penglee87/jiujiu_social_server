from flask import jsonify, request, g, url_for, current_app
from app import db
from app.models import User, Post, Permission
from . import api_bl
from .decorators import permission_required
from .errors import forbidden


@api_bl.route('/posts/')
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

    def post_to_json(post):
        author = User.query.get(post.author_id)
        json_post = {
            'url': url_for(f'{request.blueprint}.get_post', id=post.id),
            'body': post.body,
            'timestamp': post.timestamp,
            'author': {
                'username': author.username,
                'avatar_hash': author.avatar_hash
            },
            'author_url': url_for(f'{request.blueprint}.get_user', id=post.author_id),
            'comments_url': url_for(f'{request.blueprint}.get_post_comments', id=post.id),
            'comment_count': post.comments.filter_by(deleted=False).count()
        }
        return json_post
    
    return jsonify({
        'posts': [post_to_json(post) for post in posts],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api_bl.route('/posts/<int:id>')
def get_post(id):
    post = Post.query.get_or_404(id)
    return jsonify(post.to_json())


@api_bl.route('/posts/', methods=['POST'])
@permission_required(Permission.WRITE)
def new_post():
    post = Post.from_json(request.json)
    post.author = g.current_user
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json()), 201, \
        {'Location': url_for(f'{request.blueprint}.get_post', id=post.id)}


@api_bl.route('/posts/<int:id>', methods=['PUT'])
@permission_required(Permission.WRITE)
def edit_post(id):
    post = Post.query.get_or_404(id)
    if g.current_user != post.author and \
            not g.current_user.can(Permission.ADMIN):
        return forbidden('Insufficient permissions')
    post.body = request.json.get('body', post.body)
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json())

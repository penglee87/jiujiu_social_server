from flask import jsonify, request, g, url_for, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Post, User, Permission, Comment
from app.services.wechat_service import get_wechat_session
from app.decorators import permission_required
from . import api_bl


@api_bl.route('/comments/')
def get_comments():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.created_at.desc()).paginate(
        page=page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_comments', page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_comments', page=page+1)
    return jsonify({
        'comments': [comment.to_json() for comment in comments],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api_bl.route('/comments/<int:id>')
def get_comment(id):
    comment = Comment.query.get_or_404(id)
    return jsonify(comment.to_json())


@api_bl.route('/posts/<int:post_id>/comments/', methods=['GET'])
def get_post_comments(post_id):
    print(f"Fetching comments for post_id: {post_id}, page: {request.args.get('page')}")
    post = Post.query.get_or_404(post_id)
    page = request.args.get('page', 1, type=int)
    pagination = post.comments.paginate(
        page=page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api_bl.get_post_comments', post_id=post_id, page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api_bl.get_post_comments', post_id=post_id, page=page+1)
    return jsonify({
        'comments': [comment.to_json() for comment in comments],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api_bl.route('/posts/<int:post_id>/comments/', methods=['POST'])
@jwt_required()
def create_post_comment(post_id):
    openid = get_jwt_identity()
    user = User.query.filter_by(openid=openid).first()

    post = Post.query.get_or_404(post_id)
    data = request.get_json()

    try:
        if user:
            body = data.get('body')
            if not body:
                return jsonify({'message': 'Comment content is required'}), 400

            comment = Comment(body=body, post_id=post_id, author_id=user.id)
            if 'parent_id' in data:
                parent = Comment.query.get(data['parent_id'])
                if parent:
                    comment.parent = parent

            db.session.add(comment)
            post.comment_count = Post.comment_count + 1
            db.session.commit()

            return jsonify({
                'message': 'Comment created successfully',
                'comment_id': comment.id,
                'author_id': user.id,
                'received_data': data
            }), 200
        else:
            return jsonify({'message': 'User not found for the given openid'}), 404
    except Exception as e:
        current_app.logger.error(f"Error occurred in create_post_comment: {e}")
        return jsonify({'message': 'An error occurred while processing the request'}), 500


@api_bl.route('/posts/<int:post_id>/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(post_id, comment_id):
    openid = get_jwt_identity()
    user = User.query.filter_by(openid=openid).first()

    try:
        if user:
            comment = Comment.query.get_or_404(comment_id)

            if comment.post_id != post_id:
                return jsonify({'message': 'Comment does not belong to the specified post'}), 400

            if comment.author_id != user.id:
                return jsonify({'message': 'User not authorized to delete this comment'}), 403

            comment.is_delete = True

            post = Post.query.get_or_404(post_id)
            post.comment_count = max(post.comment_count - 1, 0)

            db.session.commit()

            return jsonify({
                'message': 'Comment deleted successfully',
                'comment_id': comment.id
            }), 200
        else:
            return jsonify({'message': 'User not found for the given openid'}), 404
    except Exception as e:
        current_app.logger.error(f"Error occurred in delete_comment: {e}")
        return jsonify({'message': 'An error occurred while processing the request'}), 500

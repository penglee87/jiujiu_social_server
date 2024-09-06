from flask import jsonify, request, current_app, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Post
from . import api_bl


@api_bl.route('/users/<int:id>')
def get_user(id):
    user = User.query.get_or_404(id)
    user_info = user.to_json()
    return jsonify({
        'message': 'User fetched successfully',
        'data': user_info
    }), 200


@api_bl.route('/users/<int:id>/posts/')
def get_user_posts(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for(f'{request.blueprint}.get_user_posts', id=id, page=page-1)
    next = None
    if pagination.has_next:
        next = url_for(f'{request.blueprint}.get_user_posts', id=id, page=page+1)

    posts_data = []
    for post in posts:
        posts_data.append(post.to_json())
    response = jsonify({
        'posts': posts_data,
        'prev': prev,
        'next': next,
        'count': pagination.total
    })
    return response

@api_bl.route('/users/<int:id>/timeline/')
def get_user_followed_posts(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.followed_posts.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_user_followed_posts', id=id, page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_user_followed_posts', id=id, page=page+1)
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })



@api_bl.route('/follow/<int:user_id>', methods=['POST'])
@jwt_required()
def follow_user(user_id):
    try:
        openid = get_jwt_identity()
        current_user = User.query.filter_by(openid=openid).first()
        user_to_follow = User.query.get(user_id)
        
        if user_to_follow is None:
            return jsonify({'message': '用户不存在'}), 404

        if current_user.is_following(user_to_follow):
            return jsonify({'message': '已经关注了该用户'}), 400

        current_user.follow(user_to_follow)
        db.session.commit()
        return jsonify({'message': '关注成功'}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'message': 'Internal Server Error', 'error': str(e)}), 500



@api_bl.route('/unfollow/<int:user_id>', methods=['POST'])
@jwt_required()
def unfollow_user(user_id):
    openid = get_jwt_identity()
    current_user = User.query.filter_by(openid=openid).first()
    user_to_unfollow = User.query.get(user_id)
    
    if user_to_unfollow is None:
        return jsonify({'message': '用户不存在'}), 404

    if not current_user.is_following(user_to_unfollow):
        return jsonify({'message': '未关注该用户'}), 400

    current_user.unfollow(user_to_unfollow)
    db.session.commit()
    return jsonify({'message': '取消关注成功'}), 200


@api_bl.route('/is_following/<int:user_id>', methods=['GET'])
@jwt_required()
def is_following(user_id):
    openid = get_jwt_identity()
    current_user = User.query.filter_by(openid=openid).first()
    user_to_check = User.query.get(user_id)
    
    if user_to_check is None:
        return jsonify({'message': '用户不存在'}), 404

    if current_user.is_following(user_to_check):
        return jsonify({'message': 'User is following'}), 200

    return jsonify({'message': 'User is not following'}), 200




@api_bl.route('/following', methods=['GET'])
@jwt_required()
def get_following():
    openid = get_jwt_identity()
    current_user = User.query.filter_by(openid=openid).first()
    
    if current_user is None:
        return jsonify({'message': '用户不存在'}), 404
    
    following = current_user.followed.all()
    #following_list = [{
    #    'user_id': follow.followed.id,
    #    'avatar_url': follow.followed.avatar_url,
    #    'nickname': follow.followed.nickname,
    #    'gender': follow.followed.gender,
    #    'birthdate': follow.followed.birthdate
    #} for follow in following]
    following_list = [follow.followed.to_json() for follow in following]
    return jsonify({'following': following_list}), 200



@api_bl.route('/followers', methods=['GET'])
@jwt_required()
def get_followers():
    openid = get_jwt_identity()
    current_user = User.query.filter_by(openid=openid).first()
    
    if current_user is None:
        return jsonify({'message': '用户不存在'}), 404
    
    followers = current_user.followers.all()
    followers_list = [follow.follower.to_json() for follow in followers]
    
    return jsonify({'followers': followers_list}), 200
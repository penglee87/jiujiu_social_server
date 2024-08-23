import datetime
from flask import jsonify, request, g, url_for, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Post, User
from . import api_bl


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

    posts_data = []
    for post in posts:
        author = User.query.get(post.author_id)
        posts_data.append({
            'id': post.id,
            'body': post.body,
            'timestamp': post.timestamp,
            'author': author.to_json(),
        })
    response = jsonify({
        'posts': posts_data,
        'prev': prev,
        'next': next,
        'count': pagination.total
    })
        
    # 设置跨源隔离所需的 HTTP 头部
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'

    return response


@api_bl.route('/posts/<int:id>')
def get_post(id):
    post = Post.query.get_or_404(id)
    author = User.query.get(post.author_id)
    
    post_data = {
        'id': post.id,
        'body': post.body,
        'post_image_url': post.post_image_url,
        'is_anon': post.is_anon,
        'timestamp': post.timestamp,
        'author': author.to_json(),
    }
    
    return jsonify(post_data)



#@api_bl.route('/create_post', methods=['POST'])
#def create_post():
#    data = request.get_json()
#    print('create_post_data', data)
#
#    try:
#        session_data = get_wechat_session(data['code'])
#        if session_data:
#            print('create_post_session_data', session_data)
#            openid = session_data.get('openid')
#            if not openid:
#                return jsonify({'message': 'WeChat API did not return openid'}), 400
#
#            user = User.query.filter_by(openid=openid).first()
#            if user:
#                body = data.get('body')
#                post_image_url = data.get('post_image_url')
#                is_anon = data.get('is_anon', False)
#
#                if not body:
#                    return jsonify({'message': 'Post content is required'}), 400
#
#                post = Post(
#                    body=body,
#                    post_image_url=post_image_url,
#                    is_anon=is_anon,
#                    author_id=user.id,  # Use the found user's id instead of current_user.id
#                    #timestamp=datetime.utcnow(),
#                    is_delete=False
#                )
#                db.session.add(post)
#                db.session.commit()
#
#                return jsonify({
#                    'message': 'Post created successfully',
#                    'post_id': post.id,
#                    'author_id': user.id,  # Use the found user's id instead of current_user.id
#                    'received_data': data
#                }), 200
#            else:
#                return jsonify({'message': 'User not found for the given openid'}), 404
#        else:
#            return jsonify({'message': 'Failed to create post due to invalid session data'}), 400
#    except Exception as e:
#        current_app.logger.error(f"Error occurred in create_post: {e}")
#        return jsonify({'message': 'An error occurred while processing the request'}), 500
   



@api_bl.route('/create_post', methods=['POST'])
@jwt_required()
def create_post():
    openid = get_jwt_identity()
    user = User.query.filter_by(openid=openid).first()
    
    if not user:
        return jsonify({'message': 'User not found'}), 404

    data = request.get_json()
    print('create_post_data', data)

    try:
        body = data.get('body')
        post_image_url = data.get('post_image_url')
        is_anon = data.get('is_anon', False)

        if not body:
            return jsonify({'message': 'Post content is required'}), 400

        post = Post(
            body=body,
            post_image_url=post_image_url,
            is_anon=is_anon,
            author_id=user.id,
            is_delete=False
        )
        db.session.add(post)
        db.session.commit()

        return jsonify({
            'message': 'Post created successfully',
            'post_id': post.id,
            'author_id': user.id,
            'received_data': data
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error occurred in create_post: {e}")
        return jsonify({'message': 'An error occurred while processing the request'}), 500

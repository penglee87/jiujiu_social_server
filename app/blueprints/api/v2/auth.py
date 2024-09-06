import requests
import os
from datetime import timedelta
from flask import current_app
#from flask_login import login_user
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models import User
from app import db
from app.services.wechat_service import get_wechat_session
from flask import request, jsonify
from . import api_bl

#@api_bl.route('/login', methods=['POST'])
#def login():
#    data = request.get_json()
#    print('login_data', data)
#
#    session_data = get_wechat_session(data['code'])
#    if session_data:
#        print('login_session_data', session_data)
#        openid = session_data['openid']
#        # 检查用户是否存在
#        user = User.query.filter_by(openid=openid).first()
#        if user:
#            login_user(user)
#            user_info = user.to_json()
#            return jsonify({'message': 'User logged in successfully',
#                            'data': user_info
#                            }), 200
#        else:
#            return jsonify({'message': 'User not found'}), 200
#    else:
#        return jsonify({'message': 'Error logging in user'}), 400

@api_bl.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    print('login_data', data)

    session_data = get_wechat_session(data['code'])
    if session_data:
        print('login_session_data', session_data)
        openid = session_data['openid']
        # 检查用户是否存在
        user = User.query.filter_by(openid=openid).first()
        if user:
            access_token = create_access_token(identity=user.openid,expires_delta=timedelta(minutes=30))
            user_info = user.to_json()
            return jsonify({'message': 'User logged in successfully',
                            'data': user_info,
                            'access_token': access_token
                            }), 200
        else:
            return jsonify({'message': 'User not found'}), 200
    else:
        return jsonify({'message': 'Error logging in user'}), 400



@api_bl.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    print('register_data', data)
    
    session_data = get_wechat_session(data['code'])
    if session_data:
        print('register_session_data', session_data)
        openid = session_data['openid']
        # 检查用户是否存在
        user = User.query.filter_by(openid=openid).first()
        if not user:
            avatar_url = data.get('avatarUrl')
            nickname = data.get('nickname')
            gender = data.get('gender')
            birthdate = data.get('birthDate')
            user = User(openid=openid, avatar_url=avatar_url, nickname=nickname, gender=gender, birthdate=birthdate)            
            db.session.add(user)
            db.session.commit()
            return jsonify({'message': 'User registered successfully'
                            }), 200
        else:
            return jsonify({'message': 'User already exists'}), 200
    else:
        return jsonify({'message': 'Error registering user'}), 400



@api_bl.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    code = request.args.get('code')
    
    if not code:
        return jsonify({'message': 'Missing code parameter'}), 400

    print('profile_code', code)

    openid = get_jwt_identity()
    user = User.query.filter_by(openid=openid).first()    

    if user:
        user_info = user.to_json()
        print('profile_user_info', user_info)
        return jsonify({
            'message': 'User logged in successfully',
            'data': user_info
        }), 200
    else:
        return jsonify({'message': 'User not found'}), 200

    


@api_bl.route('/profile_edit', methods=['POST'])
@jwt_required()
def profile_edit():
    data = request.get_json()
    print('profile_edit_data', data)
    
    try:
       openid = get_jwt_identity()
       if not openid:
           return jsonify({'message': 'WeChat API did not return openid'}), 400
       
       user = User.query.filter_by(openid=openid).first()
       if user:
           avatar_url = data.get('avatarUrl')
           nickname = data.get('nickname')
           gender = data.get('gender')
           birthdate = data.get('birthDate')
           user.avatar_url = avatar_url
           user.nickname = nickname
           user.gender = gender
           user.birthdate = birthdate
           db.session.commit()
           user_info = user.to_json()
           return jsonify({'message': 'User profile edited successfully',
                           'data': user_info
                           }), 200
       else:
           return jsonify({'message': 'User not found'}), 404

    except Exception as e:
        current_app.logger.error(f"Error occurred in profile_edit: {e}")
        return jsonify({'message': 'Internal Server Error'}), 500


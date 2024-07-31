import requests
import os
from flask import current_app
from app.models import User, Wx_User
from app import db
from app.services.file_service import FileService
from flask import request, jsonify
from . import api_bl



@api_bl.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    print('login_data', data)
    # 调用微信API获取用户信息
    response = requests.get('https://api.weixin.qq.com/sns/jscode2session', params={
        'appid': current_app.config['WECHAT_APPID'],
        'secret': current_app.config['WECHAT_APPSECRET'],
        'js_code': data['code'],
        'grant_type': 'authorization_code'
    })
    if response.status_code == 200:
        session_data = response.json()
        print('login_session_data',session_data)
        openid = session_data['openid']
        # 检查用户是否存在
        user = Wx_User.query.filter_by(openid=openid).first()
        if user:
            user_info = {
                'avatarUrl': user.avatar_url,
                'nickName': user.nickname,
                'gender': user.gender,
                'birthDate': user.birthdate,
            }
            return jsonify({'message': 'User logged in successfully',
                            'data': user_info                            
                            }), 200
        else:
            return jsonify({'message': 'User not found'}), 200
    else:
        return jsonify({'message': 'Error logging in user'}), 400
    


@api_bl.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        data = request.get_json()
        code = data.get('code')
    else:
        code = request.args.get('code')
    
    if not code:
        return jsonify({'message': 'Missing code parameter'}), 400

    print('profile_code', code)
    # 调用微信API获取用户信息
    response = requests.get('https://api.weixin.qq.com/sns/jscode2session', params={
        'appid': current_app.config['WECHAT_APPID'],
        'secret': current_app.config['WECHAT_APPSECRET'],
        'js_code': code,
        'grant_type': 'authorization_code'
    })
    if response.status_code == 200:
        session_data = response.json()
        print('profile_session_data',session_data)
        openid = session_data['openid']
        if not openid:
            return jsonify({'message': 'Failed to get openid from WeChat API'}), 400
        
        # 检查用户是否存在
        user = Wx_User.query.filter_by(openid=openid).first()
        if user:
            user_info = {
                'avatarUrl': user.avatar_url,
                'nickName': user.nickname,
                'gender': user.gender,
                'birthDate': user.birthdate,
            }
            print('user_info', user_info)
            return jsonify({
                'message': 'User logged in successfully',
                'data': user_info
            }), 200
        else:
            print('User not found')
            return jsonify({'message': 'User not found'}), 200
    else:
        print('Error logging in user', response.status_code, response.text)
        return jsonify({'message': 'Error logging in user'}), 400


#@api_bl.route('/register_bak', methods=['POST'])
#def register_bak():
#    data = request.get_json()
#    response = AuthService.register_bak(data)
#    return jsonify(response)
#
@api_bl.route('/register', methods=['POST'])
def register():
    # 调用微信API获取用户信息(头像上传至服务器)
    data = request.get_json()
    print('register_data', data)
    response = requests.get('https://api.weixin.qq.com/sns/jscode2session', params={
        'appid': current_app.config['WECHAT_APPID'],
        'secret': current_app.config['WECHAT_APPSECRET'],
        'js_code': data['code'],
        'grant_type': 'authorization_code'
    })
    if response.status_code == 200:
        session_data = response.json()
        print('register_session_data', session_data)
        openid = session_data['openid']
        # 检查用户是否存在
        user = Wx_User.query.filter_by(openid=openid).first()
        print('useruser',user)
        if not user:
            nickname = data.get('nickname')
            avatar_url = data.get('avatarUrl')
            gender = data.get('gender')
            birthdate = data.get('birthDate')
            print('if not user',nickname,avatar_url,gender,birthdate)
            user = Wx_User(openid=openid, nickname=nickname, avatar_url=avatar_url, gender=gender, birthdate=birthdate)
            db.session.add(user)
            db.session.commit()
            return jsonify({'message': 'User registered successfully'}), 200
        else:
            return jsonify({'message': 'User already exists'}), 200
    else:
        return jsonify({'message': 'Error registering user'}), 400

#
#@api_bl.route('/login', methods=['POST'])
#def login():
#    data = request.get_json()
#    response = AuthService.login(data)
#    return jsonify(response)
#
#@api_bl.route('/user_edit', methods=['POST'])
#def user_edit():
#    data = request.form.to_dict()
#    file = request.files.get('avatar')
#    response = AuthService.user_edit(data,file)
#    return jsonify(response)


@api_bl.route('/profile_update', methods=['POST'])
def profile_update():
    # 调用微信API获取用户信息(头像上传至服务器)
    data = request.get_json()
    print('profile_update_data', data)
    try:
        # 调用微信API获取用户信息
        response = requests.get('https://api.weixin.qq.com/sns/jscode2session', params={
            'appid': current_app.config['WECHAT_APPID'],
            'secret': current_app.config['WECHAT_APPSECRET'],
            'js_code': data['code'],
            'grant_type': 'authorization_code'
        })
        if response.status_code == 200:
            session_data = response.json()
            print('profile_update_session_data', session_data)
            if 'openid' not in session_data:
                return {'message': 'WeChat API did not return openid'}, 400
            openid = session_data['openid']
            # 检查用户是否存在
            user = Wx_User.query.filter_by(openid=openid).first()
            print('old_user', user)
            if user:
                avatar_url = data.get('avatarUrl')
                nickname = data.get('nickname')
                gender = data.get('gender')
                birthdate = data.get('birthDate')
                print('if user',nickname,avatar_url,gender,birthdate)
                #user = Wx_User(openid=openid, nickname=nickname, avatar_url=avatar_url, gender=gender, birthdate=birthdate)
                user.avatar_url = avatar_url
                user.nickname = nickname
                user.gender = gender
                user.birthdate = birthdate
                print('new_user',user)
                db.session.commit()
                print('new_user_commit')
                return {'message': 'User profile updated successfully', 
                        'userInfo': {
                            'avatarUrl': user.avatar_url,
                            'nickName': user.nickname,
                            'gender': user.gender,
                            'birthDate': user.birthdate,
                        }}, 200
            else:
                return {'message': 'User not found'}, 404
        return {'message': 'Error updating user profile'}, 400
    except Exception as e:
        current_app.logger.error(f"Error occurred in user_edit: {e}")
        return {'message': 'Internal Server Error'}, 500




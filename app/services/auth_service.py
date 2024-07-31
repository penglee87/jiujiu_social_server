import requests
import os
from flask import current_app
from app.models import User, Wx_User
from app import db
from app.services.file_service import FileService

class AuthService:
    @staticmethod
    def register_bak(data):
        # 调用微信API获取用户信息(头像未上传至服务器)
        print('register_data',data)
        response = requests.get('https://api.weixin.qq.com/sns/jscode2session', params={
            'appid': current_app.config['WECHAT_APPID'],
            'secret': current_app.config['WECHAT_APPSECRET'],
            'js_code': data['code'],
            'grant_type': 'authorization_code'
        })
        if response.status_code == 200:
            session_data = response.json()
            print('register_session_data',session_data)
            openid = session_data['openid']
            # 检查用户是否存在
            user = Wx_User.query.filter_by(openid=openid).first()
            if not user:
                user = Wx_User(openid=openid, nickname=data.get('nickname'), avatar_url=data.get('avatarUrl'))
                db.session.add(user)
                db.session.commit()
            return {'message': 'User registered successfully'}
        return {'message': 'Error registering user'}, 400
    
    
    @staticmethod
    def register(data, file=None):
        # 调用微信API获取用户信息(头像上传至服务器)
        print('register_data', data)
        print('register_file', file)
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
            if not user:
                nickname = data.get('nickname')
                avatar_url = None
                if file:
                    avatar_url = FileService.save_image('avatars', file)
                if avatar_url:
                    user = Wx_User(openid=openid, nickname=nickname, avatar_url=avatar_url)
                    db.session.add(user)
                    db.session.commit()
            return {'message': 'User registered successfully'}
        return {'message': 'Error registering user'}, 400

    @staticmethod
    def login(data):
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
                return {'message': 'User logged in successfully'}
            return {'message': 'User not found'}, 404
        return {'message': 'Error logging in user'}, 400
    
    @staticmethod
    def user_edit(data, file=None):
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
                print('update_profile_session_data', session_data)
                if 'openid' not in session_data:
                    return {'message': 'WeChat API did not return openid'}, 400
                openid = session_data['openid']
                # 检查用户是否存在
                user = Wx_User.query.filter_by(openid=openid).first()
                print('user_exists', user)
                print('file', type(file),file)
                if user:
                    user.nickname = data.get('nickname', user.nickname)

                    # 处理文件上传
                    if file:
                        avatar_url = FileService.save_image('avatars', file)
                        if avatar_url:
                            user.avatar_url = avatar_url
                    db.session.commit()
                    return {'message': 'User profile updated successfully', 
                            'userInfo': {
                                'avatarUrl': user.avatar_url,
                                'nickName': user.nickname,
                            }}, 200
                return {'message': 'User not found'}, 404
            return {'message': 'Error updating user profile'}, 400
        except Exception as e:
            current_app.logger.error(f"Error occurred in user_edit: {e}")
            return {'message': 'Internal Server Error'}, 500
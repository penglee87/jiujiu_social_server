import requests
from flask import current_app

def get_wechat_session(js_code):
    response = requests.get('https://api.weixin.qq.com/sns/jscode2session', params={
        'appid': current_app.config['WECHAT_APPID'],
        'secret': current_app.config['WECHAT_APPSECRET'],
        'js_code': js_code,
        'grant_type': 'authorization_code'
    })
    if response.status_code == 200:
        session_data = response.json()
        return session_data
    return None
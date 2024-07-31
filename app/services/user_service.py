from app.models import User

def create_user(data):
    user = User(name=data['name'], email=data['email'])
    # 其他业务逻辑，如密码加密等
    user.save()
    return user

def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found")
    return user

def update_user(user_id, data):
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found")
    # 更新用户信息
    user.name = data.get('name', user.name)
    user.email = data.get('email', user.email)
    user.save()
    return user
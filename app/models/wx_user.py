from datetime import datetime
from app import db


class Wx_User(db.Model):
    __tablename__ = 'wx_users'
    id = db.Column(db.Integer, primary_key=True)
    openid = db.Column(db.String(64), nullable=False, unique=True, comment='微信openid')
    nickname = db.Column(db.String(32), comment='昵称')
    avatar_url = db.Column(db.String(256), comment='头像')
    gender = db.Column(db.String(64), comment='性别')
    birthdate = db.Column(db.Date)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)
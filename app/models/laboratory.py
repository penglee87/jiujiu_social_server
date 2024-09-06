
from datetime import datetime
from app import db

# 默契度实验室问题类
class LabQuestion(db.Model):
    __tablename__ = 'lab_questions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    question_class = db.Column(db.String(64))  # 问题分类
    question_body = db.Column(db.Text)  # 问题内容
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_delete = db.Column(db.Boolean, default=False)

    author = db.relationship('User', back_populates='lab_questions')

# 用户默契度实验室类
class LabRoom(db.Model):
    __tablename__ = 'lab_rooms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_delete = db.Column(db.Boolean, default=False)

    lab_messages = db.relationship('LabMessage', back_populates='lab_room', lazy='dynamic')
    users = db.relationship('User', secondary='user_lab_rooms', back_populates='lab_rooms')

# 用户默契度实验室关系表
class UserLabRoom(db.Model):
    __tablename__ = 'user_lab_rooms'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    lab_room_id = db.Column(db.Integer, db.ForeignKey('lab_rooms.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    db.UniqueConstraint('user_id', 'lab_room_id', name='unique_user_lab_room')


# 默契度实验室消息类
class LabMessage(db.Model):
    __tablename__ = 'lab_messages'
    id = db.Column(db.Integer, primary_key=True)
    lab_room_id = db.Column(db.Integer, db.ForeignKey('lab_rooms.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('lab_questions.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    answer = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_delete = db.Column(db.Boolean, default=False)
    
    author = db.relationship('User', back_populates='lab_messages')
    lab_room = db.relationship('LabRoom', back_populates='lab_messages')
    question = db.relationship('LabQuestion')

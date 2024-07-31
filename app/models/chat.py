
from datetime import datetime
from app import db
from app.exceptions import ValidationError

# 用户聊天室类
class ChatRoom(db.Model):
    __tablename__ = 'chat_rooms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    is_delete = db.Column(db.Boolean, default=False)
    messages = db.relationship('Message', back_populates='chat_room', lazy='dynamic')
    users = db.relationship('User', secondary='user_chat_rooms', back_populates='chat_rooms')

# 用户聊天室关系表
class UserChatRoom(db.Model):
    __tablename__ = 'user_chat_rooms'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    chat_room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    db.UniqueConstraint('user_id', 'chat_room_id', name='unique_user_chat_room')


# 消息类
class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chat_room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=True)
    is_delete = db.Column(db.Boolean, default=False)
    
    author = db.relationship('User', back_populates='messages')
    chat_room = db.relationship('ChatRoom', back_populates='messages')

    def to_json(self):
        json_message = {
            'id': self.id,
            'body': self.body,
            'timestamp': self.timestamp.isoformat() + 'Z',
            'author_id': self.author_id,
            'chat_room_id': self.chat_room_id,
        }
        if self.author:
            json_message['author'] = {
                'id': self.author.user_id,
                'nikename': self.author.nikename,
            }
        return json_message

    @staticmethod
    def from_json(json_message):
        body = json_message.get('body')
        if not body:
            raise ValidationError('Message does not have a body')
        return Message(body=body)
    


from datetime import datetime
from app import db
from app.exceptions import ValidationError

# 用户聊天室类
class ChatRoom(db.Model):
    __tablename__ = 'chat_rooms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_delete = db.Column(db.Boolean, default=False)

    chat_messages = db.relationship('ChatMessage', back_populates='chat_room', lazy='dynamic')
    users = db.relationship('User', secondary='user_chat_rooms', back_populates='chat_rooms')

    def increment_unread_count(self, user):
        user_chat_room = UserChatRoom.query.filter_by(user_id=user.id, chat_room_id=self.id).first()
        if user_chat_room:
            user_chat_room.unread_count += 1
            db.session.commit()

    def mark_as_read(self, user):
        user_chat_room = UserChatRoom.query.filter_by(user_id=user.id, chat_room_id=self.id).first()
        if user_chat_room:
            user_chat_room.unread_count = 0
            db.session.commit()

    def unread_messages(self, user):
        user_chat_room = UserChatRoom.query.filter_by(user_id=user.id, chat_room_id=self.id).first()
        if user_chat_room:
            return user_chat_room.unread_count
        return 0

# 用户聊天室关系表
class UserChatRoom(db.Model):
    __tablename__ = 'user_chat_rooms'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    chat_room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    unread_count = db.Column(db.Integer, default=0)
    is_delete = db.Column(db.Boolean, default=False)
    db.UniqueConstraint('user_id', 'chat_room_id', name='unique_user_chat_room')


# 消息类
class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chat_room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_delete = db.Column(db.Boolean, default=False)
    
    author = db.relationship('User', back_populates='chat_messages')
    chat_room = db.relationship('ChatRoom', back_populates='chat_messages')

    def to_json(self):
        json_message = {
            'id': self.id,
            'body': self.body,
            'created_at': self.created_at.isoformat() + 'Z',
            'chat_room_id': self.chat_room_id,
        }
        if self.author:
            json_message['author'] = {
                'id': self.author.id,
                'nickname': self.author.nickname,
            }
        return json_message

    @staticmethod
    def from_json(json_message):
        body = json_message.get('body')
        if not body:
            raise ValidationError('Message does not have a body')
        return ChatMessage(body=body)
    

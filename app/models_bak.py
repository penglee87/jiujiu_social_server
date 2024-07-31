from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.jose import jwt
import time
from markdown import markdown
import bleach
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin
from app.exceptions import ValidationError
from . import db, login_manager


class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT,
                          Permission.WRITE, Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT,
                              Permission.WRITE, Permission.MODERATE,
                              Permission.ADMIN],
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def __repr__(self):
        return '<Role %r>' % self.name


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    messages = db.relationship('Message', back_populates ='author')
    chat_rooms = db.relationship('ChatRoom', secondary='user_chat_rooms', back_populates='users')


    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()
        self.follow(self)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    #生成确认邮箱的令牌
    def generate_confirmation_token(self, expiration=3600):
        # Create a JWT token with expiration
        header = {'alg': 'HS256'}  # Use HS256 algorithm for signing
        payload = {'confirm': self.id, 'exp': time.time() + expiration}  # Include confirmation data and expiration
        secret_key = current_app.config['SECRET_KEY']
        return jwt.encode(header, payload, secret_key).decode('utf-8')

    #确认用户邮箱
    def confirm(self, token):
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'])
            data = payload.get('confirm')
        except:
            return False
        if data != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    #生成重置密码的令牌
    def generate_reset_token(self, expiration=3600):
        header = {'alg': 'HS256'}  # Use HS256 algorithm for signing
        payload = {'reset': self.id, 'exp': time.time() + expiration}  # Include confirmation data and expiration
        secret_key = current_app.config['SECRET_KEY']
        return jwt.encode(header, payload, secret_key).decode('utf-8')
    
    @staticmethod
    def reset_password(token, new_password):
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'])
        except:
            return False
        user = User.query.get(payload.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    #修改邮箱
    def generate_email_change_token(self, new_email, expiration=3600):
        header = {'alg': 'HS256'}  # Use HS256 algorithm for signing
        payload = {'change_email': self.id, 'new_email': new_email, 'exp': time.time() + expiration}  # Include confirmation data and expiration
        secret_key = current_app.config['SECRET_KEY']
        return jwt.encode(header,payload, secret_key).decode('utf-8')
    
    def change_email(self, token):
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'])
        except:
            return False
        if payload.get('change_email') != self.id:
            return False
        new_email = payload.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

    def gravatar(self, size=100, default='identicon', rating='g'):
        url = 'https://secure.gravatar.com/avatar'
        hash = self.avatar_hash or self.gravatar_hash()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        if user.id is None:
            return False
        return self.followed.filter_by(
            followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        if user.id is None:
            return False
        return self.followers.filter_by(
            follower_id=user.id).first() is not None

    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id)\
            .filter(Follow.follower_id == self.id)

    def to_json(self):
        json_user = {
            'url': url_for('api.get_user', id=self.id),
            'username': self.username,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'posts_url': url_for('api.get_user_posts', id=self.id),
            'followed_posts_url': url_for('api.get_user_followed_posts',
                                          id=self.id),
            'post_count': self.posts.count()
        }
        return json_user

    def generate_auth_token(self, expiration):
        header = {'alg': 'HS256'}
        payload = {'id': self.id, 'exp': time.time() + expiration}
        secret_key = current_app.config['SECRET_KEY']
        return jwt.encode(header, payload, secret_key).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'])
            user_id = payload.get('id')
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    def to_json(self):
        json_post = {
            'url': url_for('api.get_post', id=self.id),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author_url': url_for('api.get_user', id=self.author_id),
            'comments_url': url_for('api.get_post_comments', id=self.id),
            'comment_count': self.comments.count()
        }
        return json_post

    @staticmethod
    def from_json(json_post):
        body = json_post.get('body')
        if body is None or body == '':
            raise ValidationError('post does not have a body')
        return Post(body=body)


db.event.listen(Post.body, 'set', Post.on_changed_body)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i',
                        'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    def to_json(self):
        json_comment = {
            'url': url_for('api.get_comment', id=self.id),
            'post_url': url_for('api.get_post', id=self.post_id),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author_url': url_for('api.get_user', id=self.author_id),
        }
        return json_comment

    @staticmethod
    def from_json(json_comment):
        body = json_comment.get('body')
        if body is None or body == '':
            raise ValidationError('comment does not have a body')
        return Comment(body=body)


db.event.listen(Comment.body, 'set', Comment.on_changed_body)

# 聊天室类
class ChatRoom(db.Model):
    __tablename__ = 'chat_rooms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    messages = db.relationship('Message', back_populates='chat_room')
    users = db.relationship('User', secondary='user_chat_rooms', back_populates='chat_rooms')


# 用户与聊天室关系表
class UserChatRoom(db.Model):
    __tablename__ = 'user_chat_rooms'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chat_room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)


# 消息类
class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chat_room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=True)
    
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
                'id': self.author.id,
                'username': self.author.username,
            }
        return json_message

    @staticmethod
    def from_json(json_message):
        body = json_message.get('body')
        if not body:
            raise ValidationError('Message does not have a body')
        return Message(body=body)


# 聊天方法
class ChatService:

    @staticmethod
    def send_message(author_id, body, chat_room_id=None):
        message = Message(author_id=author_id, body=body, chat_room_id=chat_room_id)
        db.session.add(message)
        db.session.commit()
        return message

    @staticmethod
    def get_messages(chat_room_id=None, limit=50):
        query = Message.query.order_by(Message.timestamp.desc())
        if chat_room_id:
            query = query.filter_by(chat_room_id=chat_room_id)
        return query.limit(limit).all()

    @staticmethod
    def add_user_to_chat_room(user_id, chat_room_id):
        user_chat_room = UserChatRoom(user_id=user_id, chat_room_id=chat_room_id)
        db.session.add(user_chat_room)
        db.session.commit()

    @staticmethod
    def get_users_in_chat_room(chat_room_id):
        chat_room = ChatRoom.query.get(chat_room_id)
        if chat_room:
            return chat_room.users
        return []

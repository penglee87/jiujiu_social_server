from datetime import datetime, timedelta
from authlib.jose import jwt, JoseError
from flask import current_app, request, url_for
from app.exceptions import ValidationError
from app import db
#from .follow import Follow
from .role import Role, Permission
from .post import Post


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    openid = db.Column(db.String(64), nullable=False, unique=True, comment='微信openid')
    avatar_url = db.Column(db.String(256), comment='头像')
    nickname = db.Column(db.String(32), comment='昵称')
    gender = db.Column(db.String(64), comment='性别')
    birthdate = db.Column(db.Date)
    city = db.Column(db.String(128), comment='城市')
    region  = db.Column(db.String(128), comment='区域')
    poster = db.Column(db.String(256), comment='封面')
    signature = db.Column(db.String(64), comment='个性签名')
    phone = db.Column(db.String(64))
    email = db.Column(db.String(64))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    location = db.Column(db.String(64), comment='当前地点')
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    last_update = db.Column(db.DateTime(), default=datetime.utcnow)
    is_delete = db.Column(db.Boolean, default=False)
    
    posts = db.relationship('Post', back_populates='author', lazy='dynamic')
    comments = db.relationship('Comment', back_populates='author', lazy='dynamic')
    chat_messages = db.relationship('ChatMessage', back_populates ='author')
    chat_rooms = db.relationship('ChatRoom', secondary='user_chat_rooms', back_populates='users')
    lab_questions = db.relationship('LabQuestion', back_populates='author')
    lab_messages = db.relationship('LabMessage', back_populates ='author')
    lab_rooms = db.relationship('LabRoom', secondary='user_lab_rooms', back_populates='users')
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


    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)
    
    #def is_moderator(self):
    #    return self.can(Permission.MODERATE)

    #def can_delete(self, item):
    #    return self.can(Permission.DELETE) and (self.id == item.author_id or self.is_administrator() or self.is_moderator())

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

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
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        if user.id is None:
            return False
        return self.followers.filter_by(follower_id=user.id).first() is not None

    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id).filter(Follow.follower_id == self.id)

    def to_json(self):
        json_user = {
            'user_id': self.id,
            'openid': self.openid,
            'avatar_url': self.avatar_url,
            'nickname': self.nickname,
            'gender': self.gender,
            'birthdate': self.birthdate,
            'city': self.city,
            'member_since': self.member_since,
            'last_seen': self.last_seen
        }
        return json_user

    def generate_jwt(self, expires_in=3600):
        now = datetime.utcnow()
        payload = {
            'user_id': self.id,
            'exp': now + timedelta(seconds=expires_in),
            'iat': now
        }
        token = jwt.encode({'alg': 'HS256'}, payload, current_app.config['JWT_SECRET_KEY'])
        return token.decode('utf-8')

    @staticmethod
    def verify_jwt(token):
        try:
            payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'])
            return User.query.get(payload['user_id'])
        except (JoseError, KeyError):
            return None

    def __repr__(self):
        return '<User %r>' % self.nickname



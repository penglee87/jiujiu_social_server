from datetime import datetime
from flask import url_for, request
from app.exceptions import ValidationError
from app import db

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    post_image_url = db.Column(db.String(256))
    is_anon = db.Column(db.Boolean, default=False, comment='是否匿名')
    like_count = db.Column(db.Integer, default=0, comment='点赞次数')
    comment_count = db.Column(db.Integer, default=0, comment='评论次数')
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    is_comments_enabled = db.Column(db.Boolean, comment='是否禁用评论')
    is_visible = db.Column(db.Boolean, comment='是否公开')
    is_delete = db.Column(db.Boolean, default=False)

    author = db.relationship('User', back_populates='posts')
    comments = db.relationship('Comment', back_populates='post', lazy='dynamic')

    def to_json(self):
        json_post = {
            'id': self.id,
            'body': self.body,
            'post_image_url': self.post_image_url,
            'is_anon': self.is_anon,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'created_at': self.created_at.isoformat() + 'Z',
            'author': self.author.to_json() if self.author else None
        }
        return json_post

    @staticmethod
    def from_json(json_post):
        body = json_post.get('body')
        if body is None or body == '':
            raise ValidationError('post does not have a body')
        return Post(body=body)
    


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)  # 父评论ID，用于追评
    is_delete = db.Column(db.Boolean, default=False)

    author = db.relationship('User', back_populates='comments')
    post = db.relationship('Post', back_populates='comments')
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic',foreign_keys=[parent_id])

    def to_json(self):
        json_comment = {
            'id': self.id,
            'body': self.body,
            'created_at': self.created_at.isoformat() + 'Z',
            'author': self.author.to_json() if self.author else None,
            'replies': [reply.to_json() for reply in self.replies if not reply.is_delete]  # 过滤掉已删除的评论
        }
        return json_comment

    @staticmethod
    def from_json(json_comment):
        body = json_comment.get('body')
        if body is None or body == '':
            raise ValidationError('comment does not have a body')
        return Comment(body=body)
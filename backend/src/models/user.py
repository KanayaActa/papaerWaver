from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    affiliation = db.Column(db.String(200))
    field_of_study = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'affiliation': self.affiliation,
            'field_of_study': self.field_of_study,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Paper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doi = db.Column(db.String(255), unique=True)
    arxiv_id = db.Column(db.String(100), unique=True)
    title = db.Column(db.Text, nullable=False)
    authors = db.Column(db.Text)
    abstract = db.Column(db.Text)
    published_date = db.Column(db.Date)
    journal = db.Column(db.String(255))
    ai_summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    added_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Paper {self.title[:50]}...>'

    def to_dict(self):
        return {
            'id': self.id,
            'doi': self.doi,
            'arxiv_id': self.arxiv_id,
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'journal': self.journal,
            'ai_summary': self.ai_summary,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'added_by': self.added_by
        }

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paper_id = db.Column(db.Integer, db.ForeignKey('paper.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    content = db.Column(db.Text, nullable=False)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='comments')
    paper = db.relationship('Paper', backref='comments')
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]))

    def __repr__(self):
        return f'<Comment {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'paper_id': self.paper_id,
            'user_id': self.user_id,
            'parent_id': self.parent_id,
            'content': self.content,
            'upvotes': self.upvotes,
            'downvotes': self.downvotes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user': self.user.to_dict() if self.user else None
        }

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    paper_id = db.Column(db.Integer, db.ForeignKey('paper.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='bookmarks')
    paper = db.relationship('Paper', backref='bookmarks')

    # Unique constraint to prevent duplicate bookmarks
    __table_args__ = (db.UniqueConstraint('user_id', 'paper_id', name='unique_user_paper_bookmark'),)

    def __repr__(self):
        return f'<Bookmark {self.user_id}-{self.paper_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'paper_id': self.paper_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'paper': self.paper.to_dict() if self.paper else None
        }

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False)
    vote_type = db.Column(db.String(10), nullable=False)  # 'upvote' or 'downvote'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='votes')
    comment = db.relationship('Comment', backref='votes')

    # Unique constraint to prevent multiple votes from same user on same comment
    __table_args__ = (db.UniqueConstraint('user_id', 'comment_id', name='unique_user_comment_vote'),)

    def __repr__(self):
        return f'<Vote {self.user_id}-{self.comment_id}-{self.vote_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'comment_id': self.comment_id,
            'vote_type': self.vote_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


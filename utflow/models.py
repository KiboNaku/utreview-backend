from utflow import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    major = db.Column(db.String(60), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    review_posted = db.relationship('Review', backref='author', lazy=True)
    reviews_liked = db.relationship('ReviewLiked', backref='user_liked', lazy=True)
    reviews_disliked = db.relationship('ReviewDisliked', backref='user_disliked', lazy=True)

    def __repr__(self):
        return f"User('{self.first_name}', '{self.last_name}', '{self.email}', '{self.major}')"

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, nullable=False)
    professor_id = db.Column(db.Integer, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    course_review = db.Column(db.Text, nullable=False)
    professor_review = db.Column(db.Text, nullable=False)
    course_rating = db.relationship('CourseRating', backref='user_review', lazy=True)
    professor_rating = db.relationship('ProfessorRating', backref='user_review', lazy=True)
    user_posted = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    users_liked = db.relationship('ReviewLiked', backref='review_liked', lazy=True)
    users_disliked = db.relationship('ReviewDisliked', backref='review_disliked', lazy=True)

    def __repr__(self):
        return f"Review('Course: {self.course_id}', 'Professor: {self.professor_id}', 'User: {self.user_posted}')"

class CourseRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    approval = db.Column(db.Boolean, nullable=False)
    usefulness = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.Integer, nullable=False)
    workload = db.Column(db.Integer, nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)

    def __repr__(self):
        return f"CourseRating('Approval: {self.approval}', 'Review: {self.review_id}'"

class ProfessorRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    approval = db.Column(db.Boolean, nullable=False)
    clear = db.Column(db.Integer, nullable=False)
    engaging = db.Column(db.Integer, nullable=False)
    grading = db.Column(db.Integer, nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)

    def __repr__(self):
        return f"ProfessorRating('Approval: {self.approval}', 'Review: {self.review_id}'"

class ReviewLiked(db.Model):
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"ReviewLiked('Review: {self.review_id}', 'User: {self.user_id}'"

class ReviewDisliked(db.Model):
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"ReviewDisliked('Review: {self.review_id}', 'User: {self.user_id}'"


from utreview import db   


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    verified = db.Column(db.Boolean, nullable=False)

    major_id = db.Column(db.Integer, db.ForeignKey('dept.id'), nullable=False)
    profile_pic_id = db.Column(db.Integer, db.ForeignKey('profile_pic.id'), nullable=False)

    reviews_posted = db.relationship('Review', backref='author', lazy=True)
    course_reviews_liked = db.relationship('CourseReviewLiked', backref='user', lazy=True)
    course_reviews_disliked = db.relationship('CourseReviewDisliked', backref='user', lazy=True)
    prof_reviews_liked = db.relationship('ProfReviewLiked', backref='user', lazy=True)
    prof_reviews_disliked = db.relationship('ProfReviewDisliked', backref='user', lazy=True)

    def __repr__(self):
        v_str = ("" if self.verified else "Not ") + "Verified"
        return f"User('{self.first_name}', '{self.last_name}', '{self.email}', '{self.major}', '{v_str}')"

class ProfilePic(db.Model): 

    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(20), unique=True, nullable=False)

    users = db.relationship('User', backref='pic', lazy=True)

    def __repr__(self):
        return f"ProfilePic('File Name: {self.file_name}')"
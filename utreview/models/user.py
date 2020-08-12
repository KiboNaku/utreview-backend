
from utreview import db   


class User(db.Model):
    """
    Class pertaining to a user of the website
    """
    id = db.Column(db.Integer, primary_key=True)

    # user data fields
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120))
    verified = db.Column(db.Boolean, nullable=False)
    other_major = db.Column(db.String(50), nullable=True)

    # id fields
    major_id = db.Column(db.Integer, db.ForeignKey('dept.id'))
    profile_pic_id = db.Column(db.Integer, db.ForeignKey('profile_pic.id'), nullable=False)

    # relationship fields
    user_courses = db.relationship('UserCourse', backref='user', lazy=True)
    reviews_posted = db.relationship('Review', backref='author', lazy=True)
    course_reviews_liked = db.relationship('CourseReviewLiked', backref='user', lazy=True)
    course_reviews_disliked = db.relationship('CourseReviewDisliked', backref='user', lazy=True)
    prof_reviews_liked = db.relationship('ProfReviewLiked', backref='user', lazy=True)
    prof_reviews_disliked = db.relationship('ProfReviewDisliked', backref='user', lazy=True)

    def __repr__(self):
        v_str = ("" if self.verified else "Not ") + "Verified"
        return f"User('{self.first_name}', '{self.last_name}', '{self.email}', '{self.major}', '{v_str}')"


class ProfilePic(db.Model):
    """
    Class pertaining to a list of possible profile pictures for users to select at the front-end
    """
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(20), unique=True, nullable=False)

    users = db.relationship('User', backref='pic', lazy=True)

    def __repr__(self):
        return f"ProfilePic('File Name: {self.file_name}')"

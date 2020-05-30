from utflow import db
from datetime import datetime


class Dept(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    abr = db.Column(db.String(3), nullable=False)
    name = db.Column(db.String(75), nullable=False)

    students = db.relationship("User", backref="major", lazy=True)
    courses = db.relationship("Course", backref="dept", lazy=True)
    scores = db.relationship("ECIS_Score", backref="dept", lazy=True)

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

class Prof(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    scores = db.relationship("ECIS_Prof_Score", backref="subject", lazy=True)
    review = db.relationship('Review', backref='subject', lazy=True)

class Course(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    num = db.Column(db.String(4), nullable=False)
    name = db.Column(db.String(75), nullable=False)
    # description = db.Column(db.String(10000), nullable=False)
    # TODO: prereq, coreq, antireq, unlocks

    dept_id = db.Column(db.Integer, db.ForeignKey('dept.id'), nullable=False)
    scores = db.relationship("ECIS_Course_Score", backref="subject", lazy=True)
    review = db.relationship('Review', backref='subject', lazy=True)


class ECIS_Prof_Score(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    
    c_num = db.Column(db.String(4), nullable=False)
    avg = db.Column(db.Double, nullable=False)
    students = db.Column(db.Integer, nullable=False)

    dept_id = db.Column(db.Integer, db.ForeignKey('dept.id'), nullable=False)
    prof_id = db.Column(db.Integer, db.ForeignKey('prof.id'), nullable=False)

    def __repr__(self):
        return f"ECIS_Prof_Score('{self.num}', '{self.avg}', '{self.students}')"


class ECIS_Course_Score(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    avg = db.Column(db.Double, nullable=False)
    students = db.Column(db.Integer, nullable=False)

    dept_id = db.Column(db.Integer, db.ForeignKey('dept.id'), nullable=False)
    prof_id = db.Column(db.Integer, db.ForeignKey('prof.id'), nullable=False)

    def __repr__(self):
        return f"ECIS_Course_Score('{self.num}', '{self.avg}', '{self.students}')"
    

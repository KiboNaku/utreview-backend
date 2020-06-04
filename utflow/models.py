from utflow import db
from datetime import datetime


class Dept(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    abr = db.Column(db.String(3), nullable=False)
    name = db.Column(db.String(75), nullable=False)

    courses = db.relationship("Course", backref="dept", lazy=True)
    students = db.relationship("User", backref="major", lazy=True)
    p_scores = db.relationship("ECIS_Prof_Score", backref="dept", lazy=True)
    c_scores = db.relationship("ECIS_Course_Score", backref="dept", lazy=True)

    def __repr__(self):
        return f"Dept('{self.abr}', '{self.name}')"


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')

    major_id = db.Column(db.Integer, db.ForeignKey('dept.id'), nullable=False)
    review_posted = db.relationship('Review', backref='author', lazy=True)
    reviews_liked = db.relationship('ReviewLiked', backref='user_liked', lazy=True)
    reviews_disliked = db.relationship('ReviewDisliked', backref='user_disliked', lazy=True)

    def __repr__(self):
        return f"User('{self.first_name}', '{self.last_name}', '{self.email}')"


class Review(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    course_review = db.Column(db.Text, nullable=False)
    professor_review = db.Column(db.Text, nullable=False)

    user_posted = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('prof.id'), nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)

    course_rating = db.relationship('CourseRating', backref='user_review', lazy=True)
    professor_rating = db.relationship('ProfessorRating', backref='user_review', lazy=True)
    users_liked = db.relationship('ReviewLiked', backref='review_liked', lazy=True)
    users_disliked = db.relationship('ReviewDisliked', backref='review_disliked', lazy=True)

    def __repr__(self):
        return f"Review('Course: {self.course_id}', 'Professor: {self.professor_id}', 'User: {self.user_posted}')"


class Prof(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    scores = db.relationship("ECIS_Prof_Score", backref="subject", lazy=True)
    reviews = db.relationship('Review', backref='prof', lazy=True)
    pc = db.relationship('Prof_Course', backref="prof", lazy=True)

    def __repr__(self):
        return f"Prof('{self.name}')"

class Course(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    num = db.Column(db.String(4), nullable=False)
    name = db.Column(db.String(75), nullable=False)
    description = db.Column(db.String(10000), nullable=False)
    # TODO: prereq, coreq, antireq, unlocks
    
    dept_id = db.Column(db.Integer, db.ForeignKey('dept.id'), nullable=True)
    
    scores = db.relationship("ECIS_Course_Score", backref="subject", lazy=True)
    reviews = db.relationship('Review', backref='course', lazy=True)
    pc = db.relationship('Prof_Course', backref="course", lazy=True)

    def __repr__(self):
        return f"Course('{self.num}', '{self.name}')"


class Prof_Course(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    prof_id = db.Column(db.Integer, db.ForeignKey('prof.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
    def __repr__(self):
        return f"Prof_Course('{self.prof_id}', '{self.course_id}')"


class ECIS_Prof_Score(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    c_num = db.Column(db.String(4), nullable=False)
    avg = db.Column(db.Float, nullable=False)
    students = db.Column(db.Integer, nullable=False)

    dept_id = db.Column(db.Integer, db.ForeignKey('dept.id'), nullable=False)
    prof_id = db.Column(db.Integer, db.ForeignKey('prof.id'), nullable=False)

    def __repr__(self):
        return f"ECIS_Prof_Score('{self.num}', '{self.avg}', '{self.students}')"


class ECIS_Course_Score(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    avg = db.Column(db.Float, nullable=False)
    students = db.Column(db.Integer, nullable=False)

    dept_id = db.Column(db.Integer, db.ForeignKey('dept.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

    def __repr__(self):
        return f"ECIS_Course_Score('{self.id}', '{self.avg}', '{self.students}')"
    

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

    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"ReviewLiked('Review: {self.review_id}', 'User: {self.user_id}'"

class ReviewDisliked(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"ReviewDisliked('Review: {self.review_id}', 'User: {self.user_id}'"


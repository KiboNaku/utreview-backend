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

    # review = db.relationship('Review', backref='author', lazy=True)

    def __repr__(self):
        return f"User('{self.first_name}', '{self.last_name}', '{self.email}', '{self.major}')"


class Prof(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    scores = db.relationship("ECIS_Prof_Score", backref="subject", lazy=True)
    review = db.relationship('Review', backref='subject', lazy=True)

    def __repr__(self):
        return f"Prof('{self.first_name}', '{self.last_name}', '{self.email}', '{self.major}')"


class Course(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    num = db.Column(db.String(4), nullable=False)
    name = db.Column(db.String(75), nullable=False)
    # description = db.Column(db.String(10000), nullable=False)
    # TODO: prereq, coreq, antireq, unlocks

    dept_id = db.Column(db.Integer, db.ForeignKey('dept.id'), nullable=False)
    scores = db.relationship("ECIS_Course_Score", backref="subject", lazy=True)
    review = db.relationship('Review', backref='subject', lazy=True)

    def __repr__(self):
        return f"User('{self.first_name}', '{self.last_name}', '{self.email}', '{self.major}')"


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

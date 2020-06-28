
from utreview import db


class Semester(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    year = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.Integer, nullable=False)

    ecis_scores = db.relationship("EcisScore", backref="semester", lazy=True)
    reviews = db.relationship("Review", backref="semester", lazy=True)
    scheduled_courses = db.relationship("ScheduledCourse", backref="semester", lazy=True)
    prof_course_sem = db.relationship('ProfCourseSemester', backref="semester", lazy=True)

    def __repr__(self):
        return f"Semester({self.year}{self.semester})"


class Dept(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)

    college = db.Column(db.String(5), default='')
    dept = db.Column(db.String(4), default='')
    abr = db.Column(db.String(3), nullable=False)
    name = db.Column(db.String(75), nullable=False)

    courses = db.relationship("Course", backref="dept", lazy=True)
    students = db.relationship("User", backref="major", lazy=True)

    def __repr__(self):
        return f"Dept(college='{self.college}', dept='{self.dept}', '{self.abr}', '{self.name}')"


class ScheduledCourse(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    unique_no = db.Column(db.Integer, nullable=False)
    session = db.Column(db.String(1), nullable=True)

    days = db.Column(db.String(10))
    time_from = db.Column(db.String(8))
    time_to = db.Column(db.String(8))
    location = db.Column(db.String(20))
    max_enrollement = db.Column(db.Integer)
    seats_taken = db.Column(db.Integer)

    sem_id = db.Column(db.Integer, db.ForeignKey("semester.id"))
    cross_listed = db.Column(db.Integer, db.ForeignKey('cross_listed.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    prof_id = db.Column(db.Integer, db.ForeignKey('prof.id'), nullable=True)

    def __repr__(self):
        return f"""ScheduledCourse(
                                    '{self.unique_no}', 
                                    '{self.prof.first_name} {self.prof.last_name}',
                                    '{self.course.dept.abr} {self.course.num}', 
                                    '{self.semester.year}{self.semester.semester}', 
                                    '{self.location}'
                                    )"""
        

class ProfCourse(db.Model):
    
    id = db.Column(db.Integer, primary_key=True) 

    prof_course_sem = db.relationship('ProfCourseSemester', backref="prof_course", lazy=True)

    prof_id = db.Column(db.Integer, db.ForeignKey('prof.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
    def __repr__(self):
        return f"""ProfCourse(
                            '{self.year}{self.semester}', 
                            '{self.prof.first_name} {self.prof.last_name}', 
                            '{self.course.dept.abr} {self.course.num}'
                            )"""


class ProfCourseSemester(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    prof_course_id = db.Column(db.Integer, db.ForeignKey('prof_course.id'), nullable=False)
    sem_id  =db.Column(db.Integer, db.ForeignKey('semester.id'), nullable=False)


from utreview import db


class Semester(db.Model):
    """
    Course pertaining to a given school semester for UT Austin
    """
    id = db.Column(db.Integer, primary_key=True)

    # data fields
    year = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.Integer, nullable=False)

    # relationship fields
    user_courses = db.relationship('UserCourse', backref='semester', lazy=True)
    reviews = db.relationship("Review", backref="semester", lazy=True)
    scheduled_courses = db.relationship("ScheduledCourse", backref="semester", lazy=True)
    prof_course_sem = db.relationship('ProfCourseSemester', backref="semester", lazy=True)

    def __repr__(self):
        return f"Semester({self.year}{self.semester})"


class Dept(db.Model):
    """
    Class pertaining to a specific department at UT Austin (for courses)
    or fields of study (for students)
    """
    id = db.Column(db.Integer, primary_key=True)

    # data fields
    abr = db.Column(db.String(3), nullable=False, unique=True)
    name = db.Column(db.String(75), nullable=False)

    college = db.Column(db.String(5), default='')
    dept = db.Column(db.String(4), default='')

    # relationship fields
    courses = db.relationship("Course", backref="dept", lazy=True)
    students = db.relationship("User", backref="major", lazy=True)

    def __repr__(self):
        return f"Dept(college='{self.college}', dept='{self.dept}', '{self.abr}', '{self.name}')"


class ScheduledCourse(db.Model):
    """
    Class pertaining to a scheduled course for a course for a specific semester
    This contains data for the times, location, and enrollment of the class
    """

    id = db.Column(db.Integer, primary_key=True)

    # data fields
    unique_no = db.Column(db.Integer, nullable=False)
    session = db.Column(db.String(1), nullable=True)

    days = db.Column(db.String(10))
    time_from = db.Column(db.String(8))
    time_to = db.Column(db.String(8))
    location = db.Column(db.String(20))
    max_enrollement = db.Column(db.Integer)
    seats_taken = db.Column(db.Integer)

    # deletion field
    mark_deletion = db.Column(db.Boolean, nullable=True, default=None)

    # id fields
    sem_id = db.Column(db.Integer, db.ForeignKey("semester.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    prof_id = db.Column(db.Integer, db.ForeignKey('prof.id'), nullable=True)
    cross_listed = db.Column(db.Integer, db.ForeignKey('cross_listed.id'), nullable=True)

    def __repr__(self):
        return f"""ScheduledCourse(
                                    '{self.unique_no}', 
                                    '',
                                    '{self.course.dept.abr} {self.course.num}', 
                                    '{self.semester.year}{self.semester.semester}', 
                                    '{self.location}'
                                    )"""
        

class ProfCourse(db.Model):
    """
    Class used to map relationships between professors and courses that shows what professors teaches what course
    """
    id = db.Column(db.Integer, primary_key=True) 

    prof_id = db.Column(db.Integer, db.ForeignKey('prof.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
    prof_course_sem = db.relationship('ProfCourseSemester', backref="prof_course", lazy=True)

    def __repr__(self):
        return f"""ProfCourse(
                            '{self.year}{self.semester}', 
                            '{self.prof.first_name} {self.prof.last_name}', 
                            '{self.course.dept.abr} {self.course.num}'
                            )"""


class ProfCourseSemester(db.Model):
    """
    Class used to map relationships between prof_course and semester. This is used to map what
    professors taught across the different semesters at UT, the unique number, and the ecis score.
    """
    id = db.Column(db.Integer, primary_key=True)
    unique_num = db.Column(db.Integer)
    prof_course_id = db.Column(db.Integer, db.ForeignKey('prof_course.id'), nullable=False)
    sem_id = db.Column(db.Integer, db.ForeignKey('semester.id'), nullable=False)
    ecis = db.relationship("EcisScore", backref="profcoursesemester", lazy=True)

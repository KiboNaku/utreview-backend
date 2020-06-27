
from utreview import db


class EcisCourseScore(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    avg = db.Column(db.Float, nullable=False)
    num_students = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.Integer, nullable=False)

    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    prof_id = db.Column(db.Integer, db.ForeignKey('prof.id'), nullable=False)

    def __repr__(self):
        return f"""EcisCourseScore(
                                '{self.year}{self.semester}', 
                                '{self.course.dept.abr} {self.course.num}', 
                                '{self.prof.first_name} {self.prof.last_name}', 
                                avg={self.avg}, 
                                num_students={self.num_students}
                                )"""


class EcisProfScore(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    
    avg = db.Column(db.Float, nullable=False)
    num_students = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.Integer, nullable=False)

    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    prof_id = db.Column(db.Integer, db.ForeignKey('prof.id'), nullable=False)

    def __repr__(self):
        return f"""EcisProfScore(
                                '{self.course.dept.abr} {self.course.num}', 
                                '{self.prof.first_name} {self.prof.last_name}', 
                                avg={self.avg}, 
                                num_students={self.num_students}
                                )"""

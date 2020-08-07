
from utreview import db


class EcisScore(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    course_avg = db.Column(db.Float, nullable=False)
    prof_avg = db.Column(db.Float, nullable=False)
    num_students = db.Column(db.Integer, nullable=False)

    prof_course_sem_id = db.Column(db.Integer, db.ForeignKey('prof_course_semester.id'), nullable=False)

    def __repr__(self):
        return f"""EcisScore(
                                '{self.year}{self.semester}', 
                                '{self.course.dept.abr} {self.course.num}', 
                                '{self.prof.first_name} {self.prof.last_name}', 
                                course_avg={self.course_avg}, prof_avg={self.prof_avg},
                                num_students={self.num_students}
                                )"""



from utreview import db

class Topic(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    courses = db.relationship("Course", backref="topic", lazy=True)

    def __repr__(self):

        parent_topic = ""
        for course in self.courses:
            if course.topic_num == 0:
                parent_topic = course.title

        return f"Topic('{parent_topic}')"


class Course(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    
    num = db.Column(db.String(6), nullable=False)
    title = db.Column(db.String(100), nullable=False)

    description = db.Column(db.Text, default="")
    restrictions = db.Column(db.Text, default="")
    pre_req = db.Column(db.Text, default="")

    # note: possible for a course to have a base topic but no further topics
    topic_num = db.Column(db.Integer, default=-1)

    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=True)
    dept_id = db.Column(db.Integer, db.ForeignKey('dept.id'), nullable=False)
    
    ecis = db.relationship("EcisScore", backref="course", lazy=True)
    reviews = db.relationship('CourseReview', backref='course', lazy=True)
    scheduled = db.relationship('ScheduledCourse', backref='course', lazy=True)
    prof_course = db.relationship('ProfCourse', backref="course", lazy=True)

    def __repr__(self):
        return f"Course('{self.dept.abr} {self.num}', '{self.title}')"


class CrossListed(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    courses = db.relationship('ScheduledCourse', backref='xlist', lazy=True)

    def __repr__(self):

        repr_strs = []
        for course in self.courses:
            repr_strs.append(f"'{course.dept.abr} {course.num}'")

        repr_str = ', \n'.join(repr_strs)

        return f"""CrossListed(
                            {repr_str}
                            )"""
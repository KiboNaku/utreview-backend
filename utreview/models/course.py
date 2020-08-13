
from utreview import db


class Topic(db.Model):
    """
    Class containing list of courses corresponding to the same topic group
    """
    id = db.Column(db.Integer, primary_key=True)
    courses = db.relationship("Course", backref="topic", lazy=True)

    def __repr__(self):

        parent_topic = ""
        for course in self.courses:
            if course.topic_num == 0:
                parent_topic = course.title

        return f"Topic('{parent_topic}')"


class UserCourse(db.Model):
    """
    Class corresponding to a course that a user took in a given semester
    """
    id = db.Column(db.Integer, primary_key=True)

    unique_num = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
    prof_id = db.Column(db.Integer, db.ForeignKey('prof.id'), nullable=True)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'), nullable=True)


class Course(db.Model):
    """
    Class corresponding to data for a course at UT Austin
    """
    id = db.Column(db.Integer, primary_key=True)

    # course catalog data fields
    num = db.Column(db.String(6), nullable=False)
    title = db.Column(db.String(100), nullable=False)

    description = db.Column(db.Text, default="")
    restrictions = db.Column(db.Text, default="")
    pre_req = db.Column(db.Text, default="")

    # note: possible for a course to have a base topic but no further topics
    topic_num = db.Column(db.Integer, default=-1)

    # ecis fields
    # update on review submission/ecis update
    ecis_avg = db.Column(db.Float, nullable=True)
    ecis_students = db.Column(db.Integer, nullable=False, default=0)
    num_ratings = db.Column(db.Integer, default=0)
    approval = db.Column(db.Float, nullable=True)
    difficulty = db.Column(db.Float, nullable=True)
    usefulness = db.Column(db.Float, nullable=True)
    workload = db.Column(db.Float, nullable=True)

    # scheduled/semester fields -> True if the course is taught at the specified semester
    current_sem = db.Column(db.Boolean, nullable=False, default=False)
    next_sem = db.Column(db.Boolean, nullable=False, default=False)
    future_sem = db.Column(db.Boolean, nullable=False, default=False)

    # id fields
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=True)
    dept_id = db.Column(db.Integer, db.ForeignKey('dept.id'), nullable=False)

    # relationship fields
    user_courses = db.relationship('UserCourse', backref='course', lazy=True)
    reviews = db.relationship('CourseReview', backref='course', lazy=True)
    scheduled = db.relationship('ScheduledCourse', backref='course', lazy=True)
    prof_course = db.relationship('ProfCourse', backref="course", lazy=True)

    def __repr__(self):
        return f"Course('{self.dept.abr} {self.num}', '{self.title}')"


class CrossListed(db.Model):
    """
    Class containing list of ScheduledCourse objects that are cross-listed
    """
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

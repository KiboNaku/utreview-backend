from utflow import db
from datetime import datetime


# TODO: check length of form inputs when string or other
# TODO: check for login, signup, review

class Dept(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    abr = db.Column(db.String(3), nullable=False)
    name = db.Column(db.String(75), nullable=False)

    courses = db.relationship("Course", backref="dept", lazy=True)
    students = db.relationship("User", backref="major", lazy=True)
    prof_scores = db.relationship("EcisProfScore", backref="dept", lazy=True)
    course_scores = db.relationship("EcisCourseScore", backref="dept", lazy=True)

    def __repr__(self):
        return f"Dept('{self.abr}', '{self.name}')"


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    verified = db.Column(db.Boolean, nullable=False)

    major_id = db.Column(db.Integer, db.ForeignKey('dept.id'), nullable=False)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'), nullable=False)

    reviews_posted = db.relationship('Review', backref='author', lazy=True)
    course_reviews_liked = db.relationship('CourseReviewLiked', backref='user', lazy=True)
    course_reviews_disliked = db.relationship('CourseReviewDisliked', backref='user', lazy=True)
    prof_reviews_liked = db.relationship('ProfReviewLiked', backref='user', lazy=True)
    prof_reviews_disliked = db.relationship('ProfReviewDisliked', backref='user', lazy=True)

    def __repr__(self):
        v_str = ("" if self.verified else "Not ") + "Verified"
        return f"User('{self.first_name}', '{self.last_name}', '{self.email}', '{v_str}', '{self.major}')"
    

# semester: only up to four years in the past

# must have prof + course combo 

# for course: must be different semesters if leaving multiple reviews
# for professor: same semester is ok

# limitations:
# for course: 5 reviews max for same course

class Review(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    course_review = db.relationship('CourseReview', backref='review', lazy=True)
    prof_review = db.relationship('ProfReview', backref='review', lazy=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Review('User: {self.author.email}', 'Course: {self.course_review.course.title}', 'Professor: {self.prof_review.prof.name}')"


class CourseReview(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    approval = db.Column(db.Boolean, nullable=False)
    usefulness = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.Integer, nullable=False)
    workload = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text, nullable=False)

    users_liked = db.relationship('CourseReviewLiked', backref='course_review', lazy=True)
    users_disliked = db.relationship('CourseReviewDisliked', backref='course_review', lazy=True)

    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)

    def __repr__(self):
        return f"CourseRating('Approval: {self.approval}')"


class ProfReview(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    approval = db.Column(db.Boolean, nullable=False)
    clear = db.Column(db.Integer, nullable=False)
    engaging = db.Column(db.Integer, nullable=False)
    grading = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text, nullable=False)
    
    users_liked = db.relationship('ProfReviewLiked', backref='prof_review', lazy=True)
    users_disliked = db.relationship('ProfReviewDisliked', backref='prof_review', lazy=True)

    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    prof_id = db.Column(db.Integer, db.ForeignKey('prof.id'), nullable=True)

    def __repr__(self):
        return f"ProfessorRating('Approval: {self.approval}', 'Review: {self.review_id}'"


class Topic(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    courses = db.relationship("Course", backref="topic", lazy=True)


class Course(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    num = db.Column(db.String(4), nullable=False)
    title = db.Column(db.String(100), nullable=False)

    description = db.Column(db.Text, default="")
    restrictions = db.Column(db.Text, default="")
    pre_req = db.Column(db.Text, default="")

    # note: possible for a course to have a base topic but no further topics
    topic_num = db.Column(db.Integer, default=-1)
    topic_name = db.Column(db.String(100), default="")

    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=True)
    dept_id = db.Column(db.Integer, db.ForeignKey('dept.id'), nullable=True)
    
    ecis = db.relationship("EcisCourseScore", backref="course", lazy=True)
    reviews = db.relationship('CourseReview', backref='course', lazy=True)
    scheduled = db.relationship('ScheduledCourse', backref='course', lazy=True)
    prof_course = db.relationship('ProfCourse', backref="course", lazy=True)

    def __repr__(self):
        return f"Course('{self.num}', '{self.name}')"

    def __str__(self):
        dept = Dept.query.filter_by(id=self.dept_id).first()
        string = ""
        string += dept.abr.lower().replace(" ", "")
        string += self.num.lower()
        return string


class Prof(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)

    ecis = db.relationship("EcisProfScore", backref="prof", lazy=True)
    reviews = db.relationship('ProfReview', backref='prof', lazy=True)
    scheduled = db.relationship('ScheduledCourse', backref='prof', lazy=True)
    prof_course = db.relationship('ProfCourse', backref="prof", lazy=True)

    def __repr__(self):
        return f"Prof('{self.name}')"

    def __str__(self):
        prof_name = self.name.split('[, ]')
        prof_content = ""
        for string in prof_name:
            prof_content += string
        return string

class ScheduledCourse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    year = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    unique_no = db.Column(db.Integer, nullable=False)

    days = db.Column(db.String(10))
    time_from = db.Column(db.Integer)
    time_to = db.Column(db.Integer)
    location = db.Column(db.String(20))
    max_enrollement = db.Column(db.Integer)
    seats_taken = db.Column(db.Integer)
    cross_listed = db.Clumn(db.Integer, db.ForeignKey('cross_listed.id'))

    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    prof_id = db.Column(db.Integer, db.ForeignKey('prof.id'), nullable=True)

    def __repr__(self):
        return f"Scheduled_Course('{self.unique_no}', '{self.location}')"

class CrossListed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    courses = db.relationship('ScheduledCourse', backref='xlist', lazy=True)

class ProfCourse(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    prof_id = db.Column(db.Integer, db.ForeignKey('prof.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
    def __repr__(self):
        return f"Prof_Course('{self.prof_id}', '{self.course_id}')"


class EcisCourseScore(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    avg = db.Column(db.Float, nullable=False)
    students = db.Column(db.Integer, nullable=False)

    dept_id = db.Column(db.Integer, db.ForeignKey('dept.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    prof_id = db.Column(db.Integer, db.ForeignKey('prof.id'), nullable=False)

    def __repr__(self):
        return f"ECIS_Course_Score('{self.id}', '{self.avg}', '{self.students}')"


class EcisProfScore(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    
    avg = db.Column(db.Float, nullable=False)
    students = db.Column(db.Integer, nullable=False)

    dept_id = db.Column(db.Integer, db.ForeignKey('dept.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    prof_id = db.Column(db.Integer, db.ForeignKey('prof.id'), nullable=False)

    def __repr__(self):
        return f"ECIS_Prof_Score('{self.num}', '{self.avg}', '{self.students}')"
    

class CourseReviewLiked(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    course_review_id = db.Column(db.Integer, db.ForeignKey('course_review.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"ReviewLiked('Review: {self.course_review_id}', 'User: {self.user_id}'"

class CourseReviewDisliked(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    course_review_id = db.Column(db.Integer, db.ForeignKey('course_review.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"ReviewDisliked('Review: {self.course_review_id}', 'User: {self.user_id}'"

class ProfReviewLiked(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    prof_review_id = db.Column(db.Integer, db.ForeignKey('prof_review.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"ReviewLiked('Review: {self.prof_review_id}', 'User: {self.user_id}'"

class ProfReviewDisliked(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    prof_review_id = db.Column(db.Integer, db.ForeignKey('prof_review.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"ReviewDisliked('Review: {self.prof_review_id}', 'User: {self.user_id}'"


class Image(db.Model): 

    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(20), nullable=False)

    user = db.relationship('User', backref='user', lazy=True)

    def __repr__(self):
        return f"Image('File Name: {self.file_name}'"
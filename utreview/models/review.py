
import datetime
from utreview import db


class Review(db.Model):
    """
    Class pertaining to a review submitted by a user
    """
    id = db.Column(db.Integer, primary_key=True)

    # data fields
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow())
    grade = db.Column(db.String(2))
    submitted = db.Column(db.Boolean, nullable=False, default=False)
    anonymous = db.Column(db.Boolean, nullable=False, default=True)

    # relationship fields
    course_review = db.relationship('CourseReview', backref='review', lazy=True)
    prof_review = db.relationship('ProfReview', backref='review', lazy=True)

    # id fields
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sem_id = db.Column(db.Integer, db.ForeignKey("semester.id"))

    def __repr__(self):
        return f"""Review(
                        'User: {self.author.email}', 
                        'Course: {self.course_review[0].course.title}', 
                        'Professor: {self.prof_review.prof.first_name} {self.prof_review.prof.last_name}'
                )"""


class CourseReview(db.Model):
    """
    Class pertaining the course section of a review
    """
    id = db.Column(db.Integer, primary_key=True)

    # course review metrics data and comments
    approval = db.Column(db.Boolean, nullable=False)
    usefulness = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.Integer, nullable=False)
    workload = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text, nullable=False)

    # relationship fields
    users_liked = db.relationship('CourseReviewLiked', backref='course_review', lazy=True)
    users_disliked = db.relationship('CourseReviewDisliked', backref='course_review', lazy=True)

    # id fields
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)

    def __repr__(self):
        return f"""CourseReview(
                                'Author: {self.review.author.email}',
                                'Approval: {self.approval}',
                                'Usefulness: {self.usefulness}',
                                'Difficulty: {self.difficulty}',
                                'Workload: {self.workload}',
                                )"""


class ProfReview(db.Model):
    """
    Class pertaining to the professor section of a review
    """
    id = db.Column(db.Integer, primary_key=True)

    # course review metrics data and comments
    approval = db.Column(db.Boolean, nullable=False)
    clear = db.Column(db.Integer, nullable=False)
    engaging = db.Column(db.Integer, nullable=False)
    grading = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text, nullable=False)

    # relationship fields
    users_liked = db.relationship('ProfReviewLiked', backref='prof_review', lazy=True)
    users_disliked = db.relationship('ProfReviewDisliked', backref='prof_review', lazy=True)

    # id fields
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    prof_id = db.Column(db.Integer, db.ForeignKey('prof.id'), nullable=True)

    def __repr__(self):
        return f"""ProfReview(
                            'Author: {self.review.author.email}',
                            'Approval: {self.approval}',
                            'Clear: {self.clear}',
                            'Engaging: {self.engaging}',
                            'Grading: {self.grading}',
                            )"""

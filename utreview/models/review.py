
from datetime import datetime
from utreview import db

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
    sem_id = db.Column(db.Integer, db.ForeignKey("semester.id"))

    def __repr__(self):
        return f"""Review(
                        'User: {self.author.email}', 
                        'Course: {self.course_review.course.title}', 
                        'Professor: {self.prof_review.prof.first_name} {self.prof_review.prof.last_name}'
                        )"""


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
        return f"""CourseReview(
                                'Author: {self.review.author.email}',
                                'Approval: {self.approval}',
                                'Usefulness: {self.usefulness}',
                                'Difficulty: {self.difficulty}',
                                'Workload: {self.workload}',
                                )"""


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
        return f"""ProfReview(
                            'Author: {self.review.author.email}',
                            'Approval: {self.approval}',
                            'Clear: {self.clear}',
                            'Engaging: {self.engaging}',
                            'Grading: {self.grading}',
                            )"""
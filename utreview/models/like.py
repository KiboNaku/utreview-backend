from utreview import db   


class CourseReviewLiked(db.Model):
    """
    Class tracking whether a course review was liked by a user
    """

    id = db.Column(db.Integer, primary_key=True)
    course_review_id = db.Column(db.Integer, db.ForeignKey('course_review.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"CourseReviewLiked(Review_id: {self.course_review_id}, User: '{self.user.email}')"


class CourseReviewDisliked(db.Model):
    """
    Class tracking whether a course review was disliked by a user
    """

    id = db.Column(db.Integer, primary_key=True)
    course_review_id = db.Column(db.Integer, db.ForeignKey('course_review.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"CourseReviewDisliked(Review_id: {self.course_review_id}, User: '{self.user.email}')"


class ProfReviewLiked(db.Model):
    """
    Class tracking whether a prof review was liked by a user
    """

    id = db.Column(db.Integer, primary_key=True)
    prof_review_id = db.Column(db.Integer, db.ForeignKey('prof_review.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"ProfReviewLiked(Review_id: {self.prof_review_id}, User: '{self.user.email}')"


class ProfReviewDisliked(db.Model):
    """
    Class tracking whether a prof review was disliked by a user
    """

    id = db.Column(db.Integer, primary_key=True)
    prof_review_id = db.Column(db.Integer, db.ForeignKey('prof_review.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"ProfReviewDisliked(Review_id: {self.prof_review_id}, User: '{self.user.email}')"

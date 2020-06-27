
from utreview import db


class Prof(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    eid = db.Column(db.String(10), unique=True)

    ecis = db.relationship("EcisScore", backref="prof", lazy=True)
    reviews = db.relationship('ProfReview', backref='prof', lazy=True)
    scheduled = db.relationship('ScheduledCourse', backref='prof', lazy=True)
    prof_course = db.relationship('ProfCourse', backref="prof", lazy=True)

    def __repr__(self):
        return f"Prof('{self.first_name} {self.last_name}')"

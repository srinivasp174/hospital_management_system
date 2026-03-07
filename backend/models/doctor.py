from extensions import db

class Doctor(db.Model):
    __tablename__ = "doctors"

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False
    )
    specialization = db.Column(db.String(100), nullable=True)
    availability = db.Column(db.Text)  # JSON string for next 7 days

    user = db.relationship(
        "User",
        backref=db.backref(
            "doctor_profile",
            uselist=False,
            cascade="all, delete"
        )
    )
    department = db.relationship(
        "Department",
        backref="doctors"
    )

from extensions import db

class Patient(db.Model):
    __tablename__ = "patients"
    
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    
    # created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    blood_group = db.Column(db.String(5))
    allergies = db.Column(db.Text)
    chronic_conditions = db.Column(db.Text)
    
    user = db.relationship(
        "User",
        backref=db.backref(
            "patient_profile",
            uselist=False,
            cascade="all, delete"
        )
    )
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
    
    availability = db.Column(db.Text) #JSON string for the next 7 days
    
    # created_at = db.Column(db.DateTime, server_default=db.func.now())
    
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

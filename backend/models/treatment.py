from extensions import db

class Treatment(db.Model):
    __tablename__ = "treatments"
    
    id = db.Column(db.Integer, primary_key=True)
    
    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey("appointments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    
    diagnosis = db.Column(db.Text, nullable=False)
    prescription = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)
    
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    appointment = db.relationship(
        "Appointment",
        backref=db.backref(
            "treatment",
            uselist=False,
            cascade="all, delete"
        )
    )
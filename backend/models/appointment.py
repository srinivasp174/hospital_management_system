import enum
from extensions import db

class AppointmentStatus(enum.Enum):
    BOOKED = "booked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Appointment(db.Model):
    __tablename__="appointments"
    
    id = db.Column(db.Integer, primary_key=True)
    
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.user_id", ondelete="RESTRICT"),
        nullable=False
    )
    
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctors.user_id",  ondelete="RESTRICT"),
        nullable=False
    )
    
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    
    status = db.Column(
        db.Enum(AppointmentStatus, name="appointment_status"),
        nullable=False,
        default=AppointmentStatus.BOOKED
    )
    
    next_visit_suggested = db.Column(db.Date)
    
    # Prevent double booking:
    __table_args__ = (
        db.UniqueConstraint(
            "doctor_id",
            "date",
            "time",
            name="unique_doctor_schedule"
        ),
    )
    
    patient = db.relationship(
        "Patient",
        backref=db.backref("appointments", lazy=True)
    )
    
    doctor = db.relationship(
        "Doctor",
        backref=db.backref("appointments", lazy=True)
    )
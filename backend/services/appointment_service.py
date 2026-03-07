from models.appointment import Appointment, AppointmentStatus
from extensions import db
from datetime import datetime

def check_conflict(doctor_id, date, time):
    """Check if doctor already has an appointment"""
    existing = Appointment.query.filter_by(
        doctor_id=doctor_id,
        date=date,
        time=time
    ).first()
    return existing is not None

def transition_status(appointment, new_status):
    """Enforce Status flow"""
    
    valid_transitions = {
        AppointmentStatus.BOOKED: [
            AppointmentStatus.COMPLETED,
            AppointmentStatus.CANCELLED
        ]
    }
    
    allowed = valid_transitions.get(appointment.status, [])
    
    if new_status not in allowed:
        return False, f"Cannot transition from {appointment.status.value} to {new_status.value}"
    
    appointment.status = new_status
    db.session.commit()
    return True,  "Status updated"

def create_appointment(doctor_id, patient_id, date, time):
    if check_conflict(doctor_id, date, time):
        return None, "Doctor already has an appointment at this date and time"
    
    appointment = Appointment(
        doctor_id=doctor_id,
        patient_id=patient_id,
        date=date,
        time=time,
        status=AppointmentStatus.BOOKED
    )
    
    db.session.add(appointment)
    db.session.commit()
    return appointment, "Appointment created"
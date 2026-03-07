from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from datetime import datetime

from extensions import db
from utils.role_required import role_required

from models.department import Department
from models.doctor import Doctor
from models.patient import Patient
from models.user import User, UserRole
from models.appointment import Appointment, AppointmentStatus
from models.treatment import Treatment

from services.appointment_service import create_appointment

patient_bp = Blueprint("patient", __name__, url_prefix="/patient")

def build_full_name(user):
    parts = [user.first_name, user.middle_name, user.last_name]
    return " ".join(p for p in parts if p)

# List Departments
@patient_bp.route("/departments", methods=["GET"])
@role_required("patient")
def list_departments():
    departments = Department.query.all()
    
    data = [
        {
            "id": d.id,
            "name": d.name,
            "description": d.description
        }
        for d in departments
    ]
    
    return jsonify(data), 200

@patient_bp.route("/doctors", methods=["GET"])
@role_required("patient")
def list_doctors():

    specialization = request.args.get("specialization")
    department = request.args.get("department")
    name = request.args.get("name")

    query = Doctor.query.join(User)

    if specialization:
        query = query.filter(
            Doctor.specialization.ilike(f"%{specialization}%")
        )

    if department:
        query = query.join(Department).filter(
            Department.name.ilike(f"%{department}%")
        )

    if name:
        query = query.filter(
            (User.first_name.ilike(f"%{name}%")) |
            (User.middle_name.ilike(f"%{name}%")) |
            (User.last_name.ilike(f"%{name}%"))
        )

    query = query.filter(User.is_active == True)

    doctors = query.all()

    result = []

    for doc in doctors:

        user = doc.user

        result.append({
            "doctor_id": doc.user_id,
            "name": build_full_name(user),
            "email": user.email,
            "phone": user.phone,
            "specialization": doc.specialization,
            "department": doc.department.name
        })

    return jsonify(result), 200

@patient_bp.route("/doctors/<int:doctor_id>", methods=["GET"])
@role_required("patient")
def doctor_details(doctor_id):
    doctor = Doctor.query.filter_by(user_id=doctor_id).first_or_404()
    user = doctor.user

    return jsonify(
        {
            "doctor_id": doctor.user_id,
            "name": build_full_name(user),
            "email": user.email,
            "phone": user.phone,
            "specialization": doctor.specialization,
            "department": doctor.department.name,
            "availability": doctor.availability
        }
    ), 200

@patient_bp.route("/doctors/<int:doctor_id>/availability", methods=["GET"])
@role_required("patient")
def doctor_availability(doctor_id):
    doctor = Doctor.query.filter_by(user_id=doctor_id).first_or_404()
    return jsonify({
        "doctor_id": doctor.user_id,
        "availability": doctor.availability
    })

@patient_bp.route("/appointments", methods=["POST"])
@role_required("patient")
def book_appointment():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400
    doctor_id = data.get("doctor_id")
    date_str = data.get("date")
    time_str = data.get("time")

    if not doctor_id or not date_str or not time_str:
        return jsonify({"error": "doctor_id, date, and time required"}), 400

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        return jsonify({"error": "Invalid date or time format"}), 400

    if date < datetime.today().date():
        return jsonify({"error": "Cannot book appointments in the past"}), 400

    patient_id = int(get_jwt_identity())

    appointment, message = create_appointment(
        doctor_id,
        patient_id,
        date,
        time
    )

    if not appointment:
        return jsonify({"error": message}), 400

    return jsonify({
        "message": message,
        "appointment_id": appointment.id
    }), 201
    
@patient_bp.route("/appointments", methods=["GET"])
@role_required("patient")
def view_appointments():
    patient_id = int(get_jwt_identity())
    
    appointments = Appointment.query.filter_by(
        patient_id=patient_id
    ).all()
    
    result = []
    
    for a in appointments:
        doctor = a.doctor.user
        
        result.append({
            "appointment_id": a.id,
            "doctor": build_full_name(doctor),
            "date": a.date.isoformat(),
            "time": a.time.strftime("%H:%M"),
            "status": a.status.value
        })
    
    return jsonify(result), 200

@patient_bp.route("/appointments/<int:appointment_id>", methods=["PUT"])
@role_required("patient")
def reschedule_appointment(appointment_id):

    patient_id = int(get_jwt_identity())
    data = request.get_json()

    date_str = data.get("date")
    time_str = data.get("time")

    if not date_str or not time_str:
        return jsonify({"error": "date and time required"}), 400

    try:
        new_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        new_time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        return jsonify({"error": "Invalid date/time format"}), 400

    appointment = Appointment.query.get_or_404(appointment_id)

    if appointment.patient_id != patient_id:
        return jsonify({"error": "Not your appointment"}), 403

    if appointment.status != AppointmentStatus.BOOKED:
        return jsonify({"error": "Cannot modify this appointment"}), 400

    # conflict check
    conflict = Appointment.query.filter_by(
        doctor_id=appointment.doctor_id,
        date=new_date,
        time=new_time
    ).first()

    if conflict and conflict.id != appointment.id:
        return jsonify({"error": "Doctor already booked at that time"}), 400

    appointment.date = new_date
    appointment.time = new_time

    db.session.commit()

    return jsonify({
        "message": "Appointment rescheduled",
        "appointment_id": appointment.id,
        "date": appointment.date.isoformat(),
        "time": appointment.time.strftime("%H:%M")
    }), 200

@patient_bp.route("/appointments/<int:appointment_id>", methods=["DELETE"])
@role_required("patient")
def cancel_appointment(appointment_id):
    patient_id = int(get_jwt_identity())
    appointment = Appointment.query.get_or_404(appointment_id)

    if appointment.patient_id != patient_id:
        return jsonify({"error": "Not your appointment"}), 403

    appointment.status = AppointmentStatus.CANCELLED
    db.session.commit()

    return jsonify({"message": "Appointment cancelled"}), 200

@patient_bp.route("/history")
@role_required("patient")
def patient_history():
    patient_id = int(get_jwt_identity())
    appointments = Appointment.query.filter_by(patient_id=patient_id).all()

    history = []
    for a in appointments:
        if not a.treatment:
            continue

        doctor = a.doctor.user

        history.append({
            "doctor": build_full_name(doctor),
            "date": a.date.isoformat(),
            "diagnosis": a.treatment.diagnosis,
            "prescription": a.treatment.prescription,
            "notes": a.treatment.notes
        })

    return jsonify(history), 200

@patient_bp.route("/profile", methods=["PUT"])
@role_required("patient")
def update_profile():
    patient_id = int(get_jwt_identity())
    user = User.query.get_or_404(patient_id)
    patient = Patient.query.filter_by(user_id=patient_id).first_or_404()
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    user.first_name = data.get("first_name", user.first_name)
    user.middle_name = data.get("middle_name", user.middle_name)
    user.last_name = data.get("last_name", user.last_name)
    user.phone = data.get("phone", user.phone)

    patient.blood_group = data.get("blood_group", patient.blood_group)
    patient.allergies = data.get("allergies", patient.allergies)
    patient.chronic_conditions = data.get("chronic_conditions", patient.chronic_conditions)

    db.session.commit()
    return jsonify({"message": "Profile updated"}), 200


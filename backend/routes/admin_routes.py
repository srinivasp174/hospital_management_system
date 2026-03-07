from flask import Blueprint, jsonify, request
from extensions import db, bcrypt
from models.user import User, UserRole
from models.doctor import Doctor
from models.patient import Patient
from models.appointment import Appointment
from utils.role_required import role_required
from datetime import date as today_date

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def build_name(user):
    """Helper function to build full name"""
    return " ".join(filter(None, [
        user.first_name,
        user.middle_name,
        user.last_name
    ]))


# Admin Dashboard
@admin_bp.route("/dashboard", methods=['GET'])
@role_required("admin")
def admin_dashboard():
    total_doctors = Doctor.query.count()
    total_patients = Patient.query.count()
    total_appointments = Appointment.query.count()

    return jsonify({
        "total_doctors": total_doctors,
        "total_patients": total_patients,
        "total_appointments": total_appointments
    }), 200
    
# Add Doctor
@admin_bp.route("/doctors", methods=["POST"])
@role_required("admin")
def add_doctor():
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Invalid request body"}), 400
    
    first_name = data.get("first_name")
    middle_name = data.get("middle_name")
    last_name = data.get("last_name")
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")

    specialization = data.get("specialization")
    department_id = data.get("department_id")
    availability = data.get("availability")
    
    if not all([first_name, last_name, email, phone, password, department_id]):
        return jsonify({"error": "Missing required fields"}), 400
    
    existing_email = User.query.filter_by(email=email).first()
    existing_phone = User.query.filter_by(phone=phone).first()
    
    if existing_email:
        return jsonify({"error": "Email already exists"}), 400
    if existing_phone:
        return jsonify({"error": "Phone already exists"}), 400
    
    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    
    user = User(
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        email=email,
        phone=phone,
        password_hash=password_hash,
        role=UserRole.DOCTOR,
        is_active=True
    )
    
    db.session.add(user)
    db.session.flush()
    
    doctor = Doctor(
        user_id = user.id,
        department_id=department_id,
        specialization=specialization,
        availability=availability
    )
    
    db.session.add(doctor)
    db.session.commit()
    
    return jsonify({"message": "Doctor created successfully"}), 201

# List Doctors
@admin_bp.route("/doctors", methods=["GET"])
@role_required("admin")
def list_doctors():
    doctors = Doctor.query.all()
    result = []
    for doctor in doctors:
        user = doctor.user
        result.append({
            "doctor_id": doctor.user_id,
            "name": build_name(user),
            "specialization": doctor.specialization,
            "department_id": doctor.department_id,
            "availability": doctor.availability,
            "active": user.is_active
        })
    return jsonify(result), 200

#Update Doctor
@admin_bp.route("/doctors/<int:id>", methods=["PUT"])
@role_required("admin")
def update_doctor(id):
    
    doctor = Doctor.query.filter_by(user_id=id).first_or_404()
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Invalid request body"}), 400
    
    doctor.specialization = data.get("specialization", doctor.specialization)
    doctor.department_id = data.get("department_id", doctor.department_id)
    doctor.availability = data.get("availability", doctor.availability)

    db.session.commit()

    return jsonify({"message": "Doctor updated"}), 200


# View Appointments
@admin_bp.route("/appointments", methods=["GET"])
@role_required("admin")
def list_appointments():
    filter_type = request.args.get("filter")  # "upcoming" or "past"
    today = today_date.today()

    query = Appointment.query
    if filter_type == "upcoming":
        query = query.filter(Appointment.date >= today)
    elif filter_type == "past":
        query = query.filter(Appointment.date < today)

    appointments = query.order_by(Appointment.date.desc()).all()
    result = []
    for appt in appointments:
        doctor_user = appt.doctor.user
        patient_user = appt.patient.user
        result.append({
            "appointment_id": appt.id,
            "doctor": build_name(doctor_user),
            "patient": build_name(patient_user),
            "date": str(appt.date),
            "time": str(appt.time),
            "status": appt.status.value
        })
    return jsonify(result), 200

# Search Doctors
@admin_bp.route("/search/doctors", methods=["GET"])
@role_required("admin")
def search_doctors():

    name = request.args.get("name")
    specialization = request.args.get("specialization")
    department_id = request.args.get("department_id")
    email = request.args.get("email")

    query = Doctor.query.join(User, Doctor.user_id == User.id)

    if specialization:
        query = query.filter(
            Doctor.specialization.ilike(f"%{specialization}%")
        )

    if department_id:
        query = query.filter(
            Doctor.department_id == department_id
        )

    if email:
        query = query.filter(
            User.email.ilike(f"%{email}%")
        )

    doctors = query.all()

    result = []

    for doctor in doctors:

        user = doctor.user

        full_name = build_name(user).lower()

        if name and name.lower() not in full_name:
            continue

        result.append({
            "doctor_id": doctor.user_id,
            "name": build_name(user),
            "specialization": doctor.specialization,
            "department_id": doctor.department_id
        })

    return jsonify(result), 200

#Search Patients
@admin_bp.route("/search/patients", methods=["GET"])
@role_required("admin")
def search_patients():

    name = request.args.get("name")
    phone = request.args.get("phone")

    patients = Patient.query.join(User).all()

    result = []

    for patient in patients:

        user = patient.user

        if name and name.lower() not in build_name(user).lower():
            continue

        if phone and phone not in user.phone:
            continue

        result.append({
            "patient_id": patient.user_id,
            "name": build_name(user),
            "phone": user.phone,
            "email": user.email
        })

    return jsonify(result), 200

# Deactivate User
@admin_bp.route("/users/<int:id>/deactivate", methods=["PUT"])
@role_required("admin")
def deactivate_user(id):

    user = User.query.get_or_404(id)

    user.is_active = False

    db.session.commit()

    return jsonify({"message": "User deactivated"}), 200


# Activate User
@admin_bp.route("/users/<int:id>/activate", methods=["PUT"])
@role_required("admin")
def activate_user(id):

    user = User.query.get_or_404(id)

    user.is_active = True

    db.session.commit()

    return jsonify({"message": "User activated"}), 200
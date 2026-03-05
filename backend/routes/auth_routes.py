import re
from datetime import timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from models.user import User, UserRole
from models.patient import Patient
from extensions import db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email)

def is_valid_phone(phone):
    return phone.isdigit() and len(phone) >= 10

def is_strong_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[!@#$%^&*(),.\":{}|<>]", password):
        return False
    
    return True

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Request must be JSON"}), 400
    required_fields = ["first_name", "last_name", "email", "phone", "password"]
    
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400
    
    first_name = data["first_name"].strip()
    middle_name = data.get("middle_name")
    last_name = data["last_name"].strip()
    email = data["email"].strip().lower()
    phone = data["phone"].strip()
    password = data["password"]
    
    if middle_name:
        middle_name = middle_name.strip()
        
    if not is_valid_email(email):
        return jsonify({"error": "Invalid email format"}), 400
    
    if not is_valid_phone(phone):
        return jsonify({"error": "Invalid phone number"}), 400
    
    if not is_strong_password(password):
        return jsonify({"error": "Password must be 8+ chars and include upper, lower, number and special character"}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400

    new_user = User(
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        phone=phone,
        email=email,
        role=UserRole.PATIENT,
        is_active=True
    )
    
    new_user.set_password(password)
    
    db.session.add(new_user)
    db.session.commit()
    
    patient_profile = Patient(user_id=new_user.id)
    db.session.add(patient_profile)
    db.session.commit()
    
    return jsonify({"message": "Patient registered successfully"}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password required"}), 400

    email = data["email"].strip().lower()
    password = data["password"]

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    if not user.is_active:
        return jsonify({"error": "Account is deactivated"}), 403

    access_token = create_access_token(
        identity=str(user.id),                          # ✅ Must be a string
        additional_claims={"role": user.role.value},    # ✅ Extra data goes here
        expires_delta=timedelta(hours=2)
    )

    return jsonify({
        "access_token": access_token,
        "user_id": user.id,
        "role": user.role.value
    }), 200
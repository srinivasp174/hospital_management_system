from flask import Blueprint
from utils.role_required import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("dashboard-test")
@role_required("admin")
def dashboard_test():
    return {"message": "Admin access working"}
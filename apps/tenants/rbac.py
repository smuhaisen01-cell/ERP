"""
RBAC — Role-Based Access Control for Saudi AI-ERP.
5 roles: super_admin, hr_manager, accountant, pos_cashier, employee
Enforced at API level via DRF permission classes.
"""
from functools import wraps
from rest_framework.permissions import BasePermission

# ─── Role Definitions ─────────────────────────────────────
ROLES = {
    "super_admin": {
        "label_ar": "مدير النظام",
        "label_en": "Super Admin",
        "modules": ["dashboard", "invoicing", "pos", "hr", "accounting", "inventory", "reports", "settings"],
    },
    "hr_manager": {
        "label_ar": "مدير الموارد البشرية",
        "label_en": "HR Manager",
        "modules": ["dashboard", "hr", "reports"],
    },
    "accountant": {
        "label_ar": "محاسب",
        "label_en": "Accountant",
        "modules": ["dashboard", "invoicing", "accounting", "reports"],
    },
    "pos_cashier": {
        "label_ar": "كاشير",
        "label_en": "POS Cashier",
        "modules": ["dashboard", "pos"],
    },
    "employee": {
        "label_ar": "موظف",
        "label_en": "Employee",
        "modules": ["dashboard", "hr_self"],
    },
}


def get_user_role(user):
    """Get role from user's profile. Falls back to 'employee' for non-staff."""
    if not user or not user.is_authenticated:
        return None
    # Check profile first
    role = getattr(user, '_cached_role', None)
    if role:
        return role
    try:
        profile = user.erp_profile
        role = profile.role
    except Exception:
        # No profile — derive from is_superuser / is_staff
        if user.is_superuser:
            role = "super_admin"
        elif user.is_staff:
            role = "super_admin"
        else:
            role = "employee"
    user._cached_role = role
    return role


def get_user_modules(user):
    """Get list of modules the user can access."""
    role = get_user_role(user)
    if not role or role not in ROLES:
        return []
    return ROLES[role]["modules"]


# ─── DRF Permission Classes ──────────────────────────────

class IsSuperAdmin(BasePermission):
    """Only super_admin can access."""
    def has_permission(self, request, view):
        return get_user_role(request.user) == "super_admin"


class IsHRManagerOrAdmin(BasePermission):
    """HR manager or super admin."""
    def has_permission(self, request, view):
        return get_user_role(request.user) in ("super_admin", "hr_manager")


class IsAccountantOrAdmin(BasePermission):
    """Accountant or super admin."""
    def has_permission(self, request, view):
        return get_user_role(request.user) in ("super_admin", "accountant")


class IsPOSCashierOrAdmin(BasePermission):
    """POS cashier or super admin."""
    def has_permission(self, request, view):
        return get_user_role(request.user) in ("super_admin", "pos_cashier")


class IsEmployeeOrAbove(BasePermission):
    """Any authenticated user (all roles)."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class HasModuleAccess(BasePermission):
    """Check if user's role has access to the required module.
    Set `required_module` on the view class."""
    def has_permission(self, request, view):
        module = getattr(view, 'required_module', None)
        if not module:
            return True
        modules = get_user_modules(request.user)
        return module in modules


class IsSelfOrHRManager(BasePermission):
    """Employee can access own data, HR manager can access all."""
    def has_object_permission(self, request, view, obj):
        role = get_user_role(request.user)
        if role in ("super_admin", "hr_manager"):
            return True
        # Employee can only access own records
        employee_field = getattr(obj, 'employee', None)
        if employee_field and hasattr(employee_field, 'user_id'):
            return employee_field.user_id == request.user.id
        if hasattr(obj, 'user_id'):
            return obj.user_id == request.user.id
        return False

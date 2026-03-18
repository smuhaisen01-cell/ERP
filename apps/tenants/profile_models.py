"""
User profile — extends auth_user with role for RBAC.
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

ROLE_CHOICES = [
    ("super_admin", "مدير النظام — Super Admin"),
    ("hr_manager", "مدير الموارد البشرية — HR Manager"),
    ("accountant", "محاسب — Accountant"),
    ("pos_cashier", "كاشير — POS Cashier"),
    ("employee", "موظف — Employee"),
]


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="erp_profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="employee")

    class Meta:
        verbose_name = "ملف المستخدم"
        verbose_name_plural = "ملفات المستخدمين"

    def __str__(self):
        return f"{self.user.username} — {self.role}"

"""
Tenant user management with RBAC role assignment.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .profile_models import UserProfile
from .rbac import ROLES, get_user_role, get_user_modules

User = get_user_model()


def ensure_profile(user):
    """Create profile if missing."""
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={"role": "super_admin" if user.is_superuser else "employee"}
    )
    return profile


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.CharField(required=False, default="employee")

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'is_active', 'is_staff', 'date_joined', 'password', 'role']
        read_only_fields = ['id', 'date_joined']

    def create(self, validated_data):
        role = validated_data.pop('role', 'employee')
        password = validated_data.pop('password')
        if role in ('super_admin', 'hr_manager', 'accountant'):
            validated_data['is_staff'] = True
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        UserProfile.objects.create(user=user, role=role)
        return user


class UserListSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    role_label = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'is_active', 'is_staff', 'date_joined', 'role', 'role_label']

    def get_role(self, obj):
        return get_user_role(obj)

    def get_role_label(self, obj):
        role = get_user_role(obj)
        return ROLES.get(role, {}).get("label_en", role)


class ChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=8)


class ChangeRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=[
        ("super_admin", "Super Admin"),
        ("hr_manager", "HR Manager"),
        ("accountant", "Accountant"),
        ("pos_cashier", "POS Cashier"),
        ("employee", "Employee"),
    ])


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        return UserSerializer

    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated, IsAdminUser
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'change_role']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        ser = ChangePasswordSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user.set_password(ser.validated_data['new_password'])
        user.save()
        return Response({'status': 'password changed'})

    @action(detail=True, methods=['post'])
    def change_role(self, request, pk=None):
        user = self.get_object()
        ser = ChangeRoleSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        role = ser.validated_data['role']
        profile = ensure_profile(user)
        profile.role = role
        profile.save()
        user.is_staff = role in ('super_admin', 'hr_manager', 'accountant')
        user.save(update_fields=['is_staff'])
        return Response({'status': 'role changed', 'role': role})

    @action(detail=False, methods=['get'])
    def me(self, request):
        user = request.user
        role = get_user_role(user)
        modules = get_user_modules(user)
        ensure_profile(user)
        employee_id = None
        employee_name = None
        try:
            from apps.hr.models import Employee
            emp = Employee.objects.filter(user=user).first()
            if emp:
                employee_id = emp.id
                employee_name = emp.name_ar
        except Exception:
            pass
        return Response({
            'id': user.id, 'username': user.username, 'email': user.email,
            'first_name': user.first_name, 'last_name': user.last_name,
            'is_staff': user.is_staff, 'is_superuser': user.is_superuser,
            'role': role, 'role_label': ROLES.get(role, {}).get('label_en', role),
            'modules': modules,
            'employee_id': employee_id, 'employee_name': employee_name,
        })

    @action(detail=False, methods=['get'])
    def roles(self, request):
        return Response([
            {"id": k, "label_ar": v["label_ar"], "label_en": v["label_en"], "modules": v["modules"]}
            for k, v in ROLES.items()
        ])

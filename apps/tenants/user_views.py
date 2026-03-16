"""
Tenant user management — create and manage users within a tenant schema.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'is_active', 'is_staff', 'date_joined', 'password']
        read_only_fields = ['id', 'date_joined']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'is_active', 'is_staff', 'date_joined']


class ChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=8)


class UserViewSet(viewsets.ModelViewSet):
    """
    Manage users within the current tenant.
    Only staff users can create/modify other users.
    """
    queryset = User.objects.all()
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        return UserSerializer

    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated, IsAdminUser
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'status': 'password changed'})

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Return current user's info."""
        return Response(UserListSerializer(request.user).data)

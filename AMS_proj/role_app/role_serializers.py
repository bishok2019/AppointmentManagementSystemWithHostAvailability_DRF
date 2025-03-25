#role_serializers.py
from .models import Role,Permission,PermissionCategory
from rest_framework import serializers
from django.db import transaction
from django.contrib.auth import get_user_model as User

from .permission_serializers import PermissionSerializer

class RoleCreateSerializer(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(queryset=Permission.objects.all(), many=True)
    class Meta:
        model = Role
        fields = ['name', 'permissions', 'created_by', 'updated_by', 'is_active']
        read_only_fields =['created_by', 'updated_by']
    
    def create(self, validated_data):
        # Extract permissions from validated_data
        permissions = validated_data.pop('permissions',[])
        # creating the role without permissions
        user = self.context['request'].user
        validated_data['created_by'] = user
        with transaction.atomic():
            role = Role.objects.create(**validated_data)
            #assigning permissions using .set()
            role.permissions.set(permissions)
            return role

class RoleListSerializer(serializers.ModelSerializer):  
    class Meta:
        model = Role
        fields = ['id', 'name', 'is_active']

class RoleDetailSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'is_active', 'permissions', 'created_by', 'updated_by']
    
    def get_permissions(self, obj):
        return obj.permissions.values('id', 'name', 'code')
    
class RoleUpdateSerializer(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(queryset=Permission.objects.all(), many=True, source='permission.name')
    class Meta:
        model = Role
        fields = ['id', 'name', 'is_active', 'permissions', 'updated_by']
        read_only_fields = ['id', 'updated_by']

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        permissions = validated_data.pop('permissions', None)
        
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if permissions is not None:
                instance.permissions.set(permissions)

        return instance
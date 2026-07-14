"""Serializers for partners app (SubCenter + SystemUser)."""
from rest_framework import serializers
from django.contrib.auth.models import User
from apps.partners.models import SubCenter, SystemUser, SubCenterUniversityMapping


class SubCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCenter
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class SystemUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    sub_center_code = serializers.CharField(source='sub_center.center_code', read_only=True)

    class Meta:
        model = SystemUser
        fields = [
            'id', 'user', 'username', 'sub_center', 'sub_center_code',
            'role', 'email', 'phone', 'is_mfa_verified', 'last_login_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = ('id', 'is_mfa_verified', 'last_login_at', 'created_at', 'updated_at')


class SystemUserCreateSerializer(serializers.ModelSerializer):
    """Creates both Django User and SystemUser in one transaction."""
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = SystemUser
        fields = ['username', 'password', 'sub_center', 'role', 'email', 'phone']

    def create(self, validated_data):
        from django.db import transaction
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        with transaction.atomic():
            user = User.objects.create_user(username=username, email=validated_data['email'], password=password)
            return SystemUser.objects.create(user=user, **validated_data)


class SubCenterUniversityMappingSerializer(serializers.ModelSerializer):
    sub_center_code = serializers.CharField(source='sub_center.center_code', read_only=True)
    university_name = serializers.CharField(source='university.name', read_only=True)

    class Meta:
        model = SubCenterUniversityMapping
        fields = ['id', 'sub_center', 'sub_center_code', 'university', 'university_name', 'created_at', 'updated_at']
        read_only_fields = ('id', 'created_at', 'updated_at', 'sub_center_code', 'university_name')

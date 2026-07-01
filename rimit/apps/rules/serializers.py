"""Serializers for rules app."""
from rest_framework import serializers
from apps.rules.models import IntakeSession, RulesConfiguration


class IntakeSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntakeSession
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class RulesConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RulesConfiguration
        fields = ['id', 'rule_name', 'description', 'conditions', 'is_active', 'priority', 'created_at', 'updated_at']
        read_only_fields = ('id', 'created_at', 'updated_at')


class EnrollmentValidationSerializer(serializers.Serializer):
    """Serializer for pre-flight /rules/validate/ endpoint."""
    student = serializers.UUIDField()
    course = serializers.UUIDField()
    session = serializers.UUIDField()

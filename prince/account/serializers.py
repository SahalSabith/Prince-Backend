from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import UserProfile

class SignupSerializer(serializers.Serializer):
    name = serializers.CharField()
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        if len(value) != 4 or not value.isdigit():
            raise serializers.ValidationError("Password must be a 4-digit number")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['phone'],  # Using phone as username
            first_name=validated_data['name'],
            password=validated_data['password']
        )
        UserProfile.objects.create(user=user, phone=validated_data['phone'])
        return user

    def to_representation(self, instance):
        return {
            'name': instance.first_name,
            'phone': instance.username,
        }

class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['phone'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid phone or password")
        data['user'] = user
        return data

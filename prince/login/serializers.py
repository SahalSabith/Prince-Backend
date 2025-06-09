from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
import phonenumbers
from phonenumbers import NumberParseException

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=4,
        max_length=4,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ('name', 'mobile', 'password')
    
    def validate_password(self, value):
        if not value.isdigit():
            raise serializers.ValidationError('Password must contain only digits')
        if len(value) != 4:
            raise serializers.ValidationError('Password must be exactly 4 digits')
        return value
    
    def validate_mobile(self, value):
        # Clean mobile number
        cleaned_mobile = ''.join(filter(str.isdigit, value))
        if len(cleaned_mobile) < 10:
            raise serializers.ValidationError('Mobile number must be at least 10 digits')
        
        # Try to parse and format
        try:
            parsed_number = phonenumbers.parse(value, None)
            if not phonenumbers.is_valid_number(parsed_number):
                raise serializers.ValidationError('Invalid mobile number')
            formatted_mobile = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            return formatted_mobile
        except NumberParseException:
            # If parsing fails, use cleaned version
            return cleaned_mobile
    
    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError('Name must be at least 2 characters long')
        return value.strip()
    
    def create(self, validated_data):
        user = User.objects.create_user(
            mobile=validated_data['mobile'],
            name=validated_data['name'],
            password=validated_data['password']
        )
        return user

class UserLoginSerializer(serializers.Serializer):
    mobile = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        min_length=4,
        max_length=4,
        style={'input_type': 'password'}
    )
    
    def validate_password(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Password must contain only digits")
        if len(value) != 4:
            raise serializers.ValidationError("Password must be exactly 4 digits")
        return value
    
    def validate(self, attrs):
        mobile = attrs.get('mobile')
        password = attrs.get('password')
        
        if mobile and password:
            # Clean mobile number for lookup
            cleaned_mobile = ''.join(filter(str.isdigit, mobile))
            
            # Try to find user with exact mobile or cleaned mobile
            user = None
            try:
                user = User.objects.get(mobile=mobile)
            except User.DoesNotExist:
                try:
                    user = User.objects.get(mobile=cleaned_mobile)
                except User.DoesNotExist:
                    pass
            
            if user and user.check_password(password):
                if not user.is_active:
                    raise serializers.ValidationError("User account is disabled")
                attrs['user'] = user
                return attrs
            
            raise serializers.ValidationError("Invalid mobile number or password")
        
        raise serializers.ValidationError("Mobile number and password are required")

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'mobile', 'date_joined', 'last_login')
        read_only_fields = ('id', 'mobile', 'date_joined', 'last_login')

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, min_length=4, max_length=4)
    new_password = serializers.CharField(write_only=True, min_length=4, max_length=4)
    
    def validate_current_password(self, value):
        if not value.isdigit():
            raise serializers.ValidationError('Password must contain only digits')
        return value
    
    def validate_new_password(self, value):
        if not value.isdigit():
            raise serializers.ValidationError('Password must contain only digits')
        if len(value) != 4:
            raise serializers.ValidationError('Password must be exactly 4 digits')
        return value
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from .models import User
from .serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer, 
    UserSerializer,
    ChangePasswordSerializer
)

class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'

class RegisterUserAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            return Response({
                'message': 'User created successfully',
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'mobile': user.mobile,
                    'date_joined': user.date_joined
                },
                'tokens': {
                    'access': str(access_token),
                    'refresh': str(refresh)
                }
            }, status=status.HTTP_201_CREATED)

        # Format field errors to single string per field
        errors = serializer.errors
        formatted_errors = {}

        for field, error_list in errors.items():
            # error_list is usually a list of strings, take first
            if isinstance(error_list, list):
                formatted_errors[field] = error_list[0]
            else:
                formatted_errors[field] = error_list

        return Response(formatted_errors, status=status.HTTP_400_BAD_REQUEST)

class LoginUserAPIView(APIView):
    """User login endpoint"""
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            return Response({
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'mobile': user.mobile,
                    'last_login': user.last_login
                },
                'tokens': {
                    'access': str(access_token),
                    'refresh': str(refresh)
                }
            }, status=status.HTTP_200_OK)

        # Clean and return a single error string
        errors = serializer.errors
        error_message = None

        if 'non_field_errors' in errors:
            error_message = errors['non_field_errors'][0]
        elif isinstance(errors, dict):
            # Get first error from the dict
            first_key = next(iter(errors))
            first_error = errors[first_key]
            if isinstance(first_error, list):
                error_message = first_error[0]
            else:
                error_message = first_error
        else:
            error_message = "Something went wrong"

        return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)

class LogoutUserAPIView(APIView):
    """User logout endpoint"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Invalid refresh token'
            }, status=status.HTTP_400_BAD_REQUEST)

class UserProfileAPIView(APIView):
    """Get and Update user profile"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user profile"""
        serializer = UserSerializer(request.user)
        return Response({
            'user': serializer.data
        }, status=status.HTTP_200_OK)
    
    def put(self, request):
        """Update user profile"""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'user': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordAPIView(APIView):
    """Change user password"""
    permission_classes = [IsAuthenticated]
    
    def put(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            current_password = serializer.validated_data['current_password']
            new_password = serializer.validated_data['new_password']
            
            if not user.check_password(current_password):
                return Response({
                    'error': 'Current password is incorrect'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(new_password)
            user.save()
            
            return Response({
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class HealthCheckAPIView(APIView):
    """Health check endpoint"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'status': 'OK',
            'timestamp': timezone.now()
        }, status=status.HTTP_200_OK)
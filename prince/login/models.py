from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.validators import RegexValidator
import phonenumbers
from phonenumbers import NumberParseException

class UserManager(BaseUserManager):
    def create_user(self, mobile, password=None, **extra_fields):
        if not mobile:
            raise ValueError('Mobile number is required')
        
        # Normalize mobile number
        try:
            parsed_number = phonenumbers.parse(mobile, None)
            mobile = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except NumberParseException:
            mobile = ''.join(filter(str.isdigit, mobile))
            
        user = self.model(mobile=mobile, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, mobile, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('name', 'Admin')
        
        return self.create_user(mobile, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    mobile = models.CharField(
        max_length=15, 
        unique=True,
        validators=[RegexValidator(regex=r'^\+?[1-9]\d{1,14}$', message='Invalid mobile number')]
    )
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'mobile'
    REQUIRED_FIELDS = ['name']
    
    class Meta:
        db_table = 'auth_user'
    
    def __str__(self):
        return f"{self.name} ({self.mobile})"
    
    def set_password(self, raw_password):
        if not raw_password or len(str(raw_password)) != 4 or not str(raw_password).isdigit():
            raise ValueError('Password must be exactly 4 digits')
        super().set_password(raw_password)

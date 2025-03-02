# Microservices Architecture Implementation with Django

This tutorial guides you through setting up a Django-based microservices architecture. We'll cover environment setup, package management, project creation, and essential configurations.

## 1. Set Up a Virtual Environment on Windows
```
python -m venv env
env\Scripts\activate
deactivate
```

## 2.  Install Required Packages
```
pip install djangorestframework python-decouple django-cors-headers gunicorn psycopg2-binary
```

## 3. Save Dependencies to a Requirements File
```
pip freeze > requirements.txt
```

## 4. Create a Django Project #1
```
django-admin startproject user_service
cd user_service
```

## 5. Create a Django App #1
```
python manage.py startapp users
```

## 6. Set Up an .env File
Create a .env file to store environment variables:
```
SECRET_KEY=
DEBUG=False
```

## 7. Configure settings.py to Use python-decouple
Modify settings.py to load environment variables securely:
```
import os
from decouple import config

# Load secret key from the .env file
SECRET_KEY = config('SECRET_KEY')

# Enable/Disable debug mode based on the .env file
DEBUG = config('DEBUG', default=False, cast=bool)
```

## 8. Register Installed Apps and Middleware
Update settings.py to include the necessary configurations:

```
ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True

INSTALLED_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'user',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]
```

## 9. Designing the User Service

### 9.1 Define the User Model
Extend Django’s built-in AbstractUser model to customize the user schema:

```
# user/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
import uuid

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        """Create and return a `User` with an email, username and password."""
        if not email:
            raise ValueError('Users Must Have an email address')
        user = self.model(email=self.normalize_email(email), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """Create and return a `User` with superuser (admin) permissions."""
        if password is None:
            raise TypeError('Superusers must have a password.')
        user = self.create_user(email, password)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        return user


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    email = models.EmailField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    # Tells Django that the UserManager class defined above should manage
    # objects of this type.
    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        db_table = "user"
```

Update settings.py to use the custom user model:
```
AUTH_USER_MODEL = 'user.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=120),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
    'ALGORITHM': 'HS256',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'id',
}
```

Run migrations:
```
python manage.py makemigrations
python manage.py migrate
```

### 9.2 Create Serializers
```
# user/serializers.py
from rest_framework import serializers
from user.models import User
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class ProviderRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255, min_length=3)
    password = serializers.CharField(
        max_length=20, min_length=6, write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        # try:
        #     prov=Provider.objects.get(user=user)
        #     token['prov'] = str(prov.id)
        # except Provider.DoesNotExist:
        #     token['prov'] = ""
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        token = self.get_token(self.user)

        # Add info outside the token data['user'] = str(self.user)
        if self.user.is_superuser:
            return data
        elif not self.user.is_verified:
            raise AuthenticationFailed('Email is not verified')
        else:
            return data
```

### 9.3 Create Views
```
# user/views.py
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from user.serializers import MyTokenObtainPairSerializer, TokenObtainPairSerializer, ProviderRegistrationSerializer
from django.conf import settings
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import IntegrityError


class LoginView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class ProviderCreate(CreateAPIView):
    serializer_class = ProviderRegistrationSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        try:
            serializer = ProviderRegistrationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            tokenData = {
                "email": request.data["email"], "password": request.data["password"]}
            tokenSerializer = TokenObtainPairSerializer(data=tokenData)
            tokenSerializer.is_valid(raise_exception=True)

            return Response(tokenSerializer.validated_data, status=status.HTTP_201_CREATED)

        except IntegrityError:
            return Response({'error': 'There is already a registered user with this email'}, status=status.HTTP_400_BAD_REQUEST)

class BlacklistRefreshView(APIView):
    def post(self, request):
        token = RefreshToken(request.data.get('refresh'))
        token.blacklist()
        return Response("Success")
```

### 9.4 Add URL Patterns
```
# user/urls.py
from django.urls import path
from user.views import LoginView, ProviderCreate, BlacklistRefreshView

urlpatterns = [
    path('login/', LoginView.as_view()),
    path('signup/', ProviderCreate.as_view()),
    path('logout/', BlacklistRefreshView.as_view()),
]
```


```
# user_service/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
]
```

### 9.5 Add user to Admin
```
# user/admin.py
from django.contrib import admin
from. models import User

admin.site.register(User)
```
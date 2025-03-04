# Microservices Architecture Implementation with Django

This tutorial guides you through setting up a Django-based microservices architecture. We will cover environment setup, package management, project creation, and essential configurations.

Example Folder Structure
```
drf-microservices/
  |-- user_service/
  |    |-- user/
  |    |-- user_service/
  |    |-- manage.py
  |    |-- .env
  |    |-- requirements.txt
  |-- post_service/
  |    |-- post/
  |    |-- post_service/
  |    |-- manage.py
  |    |-- .env
  |    |-- requirements.txt
  |-- README.md  
```

## 1. Set Up a Virtual Environment on Windows
```
python -m venv env
env\Scripts\activate
deactivate
```

To deactivate:
```
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

## 4. Create a Django Project
```
django-admin startproject user_service
cd user_service
```

## 5. Create a Django App
```
python manage.py startapp users
```

## 6. Set Up an .env File
Create a .env file to store environment variables:
```
SECRET_KEY=
DEBUG=False
JWT_SECRET_KEY=
```

Modify settings.py to load environment variables securely:
```
import os
from decouple import config

# Load secret key from the .env file
SECRET_KEY = config('SECRET_KEY')

# Enable/Disable debug mode based on the .env file
DEBUG = config('DEBUG', default=False, cast=bool)
```

## 7. Register Installed Apps and Middleware
Update settings.py to include the necessary configurations:

```
ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True

INSTALLED_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',    
    'user', # Name of the app
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

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
    "SIGNING_KEY": config('JWT_SECRET_KEY'),
    'ALGORITHM': 'HS256',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'id',
}
```

## 8. Designing the User Service
### 8.1 Create a Custom User Model
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
```

Run migrations:
```
python manage.py makemigrations
python manage.py migrate
```

### 8.2 Create Serializers
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

### 8.3 Create Views
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

### 8.4 Add URL Patterns
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

### 8.5 Add user to Admin
```
# user/admin.py
from django.contrib import admin
from. models import User

admin.site.register(User)
```

Create a superuser:
```
python manage.py createsuperuser
```

### 8.6 Serve Static and Media Files
Update settings.py
```
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
MEDIA_URL = '/media/'
```

Run:
```
python manage.py collectstatic
```

### 8.6  Use Docker for Containerization
```
# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables (optional)
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

COPY requirements.txt .

# Install dependencies in a single step (reduces layer size)
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Start the Django app using Gunicorn
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 9. Navigate to the drf-microservices directory
```
cd..
```

## 10. Create a Django 
```
django-admin startproject post_service
cd post_service
```

## 11. Create a Django App
```
python manage.py startapp post
```

## 13. Repeat step 1,2,3,6,7
- Set Up a Virtual Environment on Windows
- Install Required Packages
- Save Dependencies to a Requirements File
- Set Up an .env File
- Configure settings.py to Use python-decouple
- Register Installed Apps and Middleware with corsheaders & post app

## 14. Designing the Post Service
### 14.1 Create Post Model
```
import uuid
from django.db import models

class Post(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    user_id = models.UUIDField()  # Storing only the user ID, not a direct FK
    title = models.CharField(max_length=100, blank=False)
    description = models.TextField(null=True, blank=True)
    created = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title']
```

### 14.2 Create Serializers
```
# post/serializers.py
from rest_framework import serializers
from post.models import Post


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'

### 14.3 Create Views
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .serializers import PostSerializer
from .models import Post


class PostListProv(APIView):
    def get(self, request):
        user_id = 'id'
        if not user_id:
            return Response({"error": "Invalid or missing token"}, status=status.HTTP_401_UNAUTHORIZED)

        # Query all posts related to the authenticated user
        posts = Post.objects.filter(user_id=user_id)
        serializer = PostSerializer(posts, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class PostCreateProv(APIView):
    def post(self, request):
        user_id = 'id'
        if not user_id:
            return Response({"error": "Invalid or missing token"}, status=status.HTTP_401_UNAUTHORIZED)

        data = request.data.copy()
        data["user_id"] = user_id  # Inject user_id into request data

        serializer = PostSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostDetailProv(APIView):
    def get(self, request, id):
        user_id = 'id'
        if not user_id:
            return Response({"error": "Invalid or missing token"}, status=status.HTTP_401_UNAUTHORIZED)
        
        post = get_object_or_404(Post, id=id, user_id=user_id)  
        serializer = PostSerializer(post)
        return Response(serializer.data)

    def put(self, request, id):
        user_id = 'id'
        if not user_id:
            return Response({"error": "Invalid or missing token"}, status=status.HTTP_401_UNAUTHORIZED)
    
        post = get_object_or_404(Post, id=id, user_id=user_id)

        serializer = PostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

### 14.4 Add URL Patterns
Include the post app's URLs in the main post_service/urls.py.

```
# post/urls.py
from django.urls import path
from post.views import PostListProv, PostCreateProv, PostDetailProv

urlpatterns = [
    path('affiliate/posts/', PostListProv.as_view()),
    path('affiliate/posts/create/', PostCreateProv.as_view()),
    path('affiliate/posts/<id>/', PostDetailProv.as_view()),
]
```

```
# post_service/urls.py
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.static import serve
from django.urls import re_path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('v1/', include('post.urls')),
]

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
]
```

### 14.5 Register Models in Admin
Ensure the Post and Category models are available in Django Admin.
```
# post/admin.py
from django.contrib import admin
from post.models import Post

admin.site.register(Post)
```

Create a superuser:
```
python manage.py createsuperuser
```

### 14.6 Serve Static and Media Files
Update settings.py

```
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
MEDIA_URL = '/media/'
```

Run:
```
python manage.py collectstatic
```
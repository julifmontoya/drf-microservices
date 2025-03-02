# Microservices Architecture Implementation with Django

This tutorial guides you through setting up a Django-based microservices architecture. We'll cover environment setup, package management, project creation, and essential configurations.

## 1. Set Up a Virtual Environment on Windows
```
python -m venv env
env\Scripts\activate
deactivate
```

## 2.  Install Required Packages
pip install djangorestframework python-decouple django-cors-headers gunicorn psycopg2-binary

## 3. Save Dependencies to a Requirements File
pip freeze > requirements.txt

## 4. Create a Django Project #1
```
django-admin startproject user_service
cd user_service
```

## 5. Create a Django App #1
python manage.py startapp users

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
    'corsheaders',
    'users',
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
# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.username
```

Update settings.py to use the custom user model:
```
AUTH_USER_MODEL = 'users.User'
```

Run migrations:
```
python manage.py makemigrations
python manage.py migrate
```

### 9.1 Create Serializers
```
# users/serializers.py
from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'address']
```
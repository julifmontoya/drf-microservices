from decouple import config
import requests
from django.conf import settings
from django.core.cache import cache

USER_SERVICE_URL = config('USER_SERVICE_URL') + "/auth/validate/"


def get_authenticated_user_id(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    # Extract token
    token = auth_header[7:]

    # Call user-service to validate token
    try:
        response = requests.post(USER_SERVICE_URL, json={"token": token}, timeout=5)
        if response.status_code == 200:
            user_id = response.json().get("user_id")
            print("user",user_id)

            # 
            print(cache.get(f"user_auth_{user_id}"))
            return user_id
            print(cache.get(f"user_auth_{user_id}"))

            # Check if user authentication was confirmed by RabbitMQ
            if cache.get(f"user_auth_{user_id}"):
                return user_id  # User is authenticated

    except requests.RequestException:
        return None

    return None
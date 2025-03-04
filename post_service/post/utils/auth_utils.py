from decouple import config
import requests
from django.conf import settings

USER_SERVICE_URL = config('USER_SERVICE_URL') + "/auth/validate/"


def get_authenticated_user_id(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]  # Extract token
    try:
        response = requests.post(USER_SERVICE_URL, json={"token": token}, timeout=5)
        if response.status_code == 200:
            return response.json().get("user_id")
    except requests.RequestException:
        return None

    return None
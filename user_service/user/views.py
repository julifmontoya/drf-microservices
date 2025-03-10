from django.shortcuts import render

# Create your views here.
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
import jwt
from decouple import config
from .utils.rabbitmq import publish_message

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


class ValidateTokenAPIView(APIView):
    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            decoded = jwt.decode(token, config("JWT_SECRET_KEY"), algorithms=["HS256"])
            user_id = decoded.get("id")

            # Publish authentication event
            publish_message("auth_events", {"user_id": user_id, "event": "token_validated"})

            return Response({"user_id": user_id}, status=status.HTTP_200_OK)
        except jwt.ExpiredSignatureError:
            return Response({"error": "Token expired"}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
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
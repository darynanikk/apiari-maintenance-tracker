import json

from django.contrib.auth.models import update_last_login
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt import settings
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers

from auth_service.utils import Util
from users.models import User


class MyTokenObtainPairSerializer(TokenObtainSerializer):
    token_class = RefreshToken

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)

        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        user = {
            "pk": self.user.pk,
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "phone": str(self.user.phone),
            "role": self.user.role
        }
        data["user"] = json.dumps(user)
        if settings.api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)

        return data


class ResetPasswordEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=2)

    class Meta:
        fields = ['email']


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=6, max_length=68, write_only=True)
    token = serializers.CharField(min_length=1, write_only=True)

    class Meta:
        fields = ['password', 'token']

    def validate(self, attrs):
        try:
            password = attrs.get('password')
            token = attrs.get('token')
            email = Util.confirm_token(token)
            user = User.objects.get(email=email)
            if not user:
                raise AuthenticationFailed('The reset link is not valid', 401)
            user.set_password(password)
            user.save()
            return user
        except Exception as ex:
            pass
        return super().validate(attrs)
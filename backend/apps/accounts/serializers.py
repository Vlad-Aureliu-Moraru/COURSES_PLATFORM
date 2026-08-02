import re

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import CommonPasswordValidator
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import PasswordResetToken, User


def validate_password_strength(value):
    if len(value) < 8:
        raise serializers.ValidationError('Parola trebuie să aibă cel puțin 8 caractere.')
    if not re.search(r'[A-Za-z]', value):
        raise serializers.ValidationError('Parola trebuie să conțină cel puțin o literă.')
    if not re.search(r'\d', value):
        raise serializers.ValidationError('Parola trebuie să conțină cel puțin o cifră.')
    try:
        CommonPasswordValidator().validate(value)
    except Exception as e:
        raise serializers.ValidationError(str(e))
    return value


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'email']


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'password2', 'first_name', 'last_name']

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Există deja un cont cu acest email.')
        return value

    def validate_password(self, value):
        return validate_password_strength(value)

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Parolele nu coincid.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        validated_data['username'] = validated_data['email']
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        return token

    def validate(self, attrs):
        authenticate_kwargs = {
            'request': self.context.get('request'),
            'email': attrs.get('email'),
            'password': attrs.get('password'),
        }
        self.user = authenticate(**authenticate_kwargs)
        if self.user is None:
            raise serializers.ValidationError('Email sau parolă incorecte.')
        if not self.user.is_active:
            raise serializers.ValidationError('Acest cont este dezactivat.')
        refresh = self.get_token(self.user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }


class RequestResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        self.user = User.objects.filter(email__iexact=value).first()
        return value


class ConfirmResetSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        return validate_password_strength(value)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password': 'Parolele nu coincid.'})
        token = PasswordResetToken.consume(attrs['token'])
        if token is None:
            raise serializers.ValidationError({'token': 'Link-ul de resetare este invalid sau expirat.'})
        attrs['_reset_instance'] = token
        return attrs

    def save(self):
        reset = self.validated_data['_reset_instance']
        user = reset.user
        user.set_password(self.validated_data['new_password'])
        user.failed_login_attempts = 0
        user.locked_until = None
        user.save(update_fields=['password', 'failed_login_attempts', 'locked_until'])
        reset.delete()
        return user

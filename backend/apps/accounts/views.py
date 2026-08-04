from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView

from .emailing import send_password_reset_email, send_signup_otp_email, send_welcome_email
from .models import PendingSignup, PasswordResetToken, User
from .serializers import (
    ConfirmResetSerializer,
    EmailTokenObtainPairSerializer,
    RequestResetSerializer,
    ResendSignupCodeSerializer,
    SignupSerializer,
    UserSerializer,
    VerifySignupSerializer,
)


class SignupThrottle(AnonRateThrottle):
    rate = '2/min'


class LoginThrottle(AnonRateThrottle):
    scope = 'login'


class PasswordResetRequestThrottle(AnonRateThrottle):
    scope = 'password_reset_request'


class SignupVerifyThrottle(AnonRateThrottle):
    scope = 'signup_verify'


class SignupResendThrottle(AnonRateThrottle):
    scope = 'signup_resend'


class LoginView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer
    throttle_classes = [LoginThrottle]


class SignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = SignupSerializer
    throttle_classes = [SignupThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        send_signup_otp_email(
            serializer.validated_data['email'], serializer._code
        )
        return Response(
            {
                'detail': 'Am trimis un cod de verificare pe email. Confirmă-l pentru a-ți activa contul.',
                'email': serializer.validated_data['email'],
            },
            status=status.HTTP_201_CREATED,
        )


class SignupVerifyView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = VerifySignupSerializer
    throttle_classes = [SignupVerifyThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_welcome_email(user.email, user.get_full_name() or user.email)
        token = EmailTokenObtainPairSerializer.get_token(user)
        return Response(
            {
                'user': UserSerializer(user).data,
                'access': str(token.access_token),
                'refresh': str(token),
            },
            status=status.HTTP_200_OK,
        )


class SignupResendView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ResendSignupCodeSerializer
    throttle_classes = [SignupResendThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pending = serializer.pending
        code = PendingSignup.add_code(pending)
        send_signup_otp_email(pending.email, code)
        return Response(
            {'detail': 'Am trimis un cod nou de activare. Verifică-ți emailul.'},
            status=status.HTTP_200_OK,
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class PasswordResetRequestView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = RequestResetSerializer
    throttle_classes = [PasswordResetRequestThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        if user is not None:
            reset, token = PasswordResetToken.create_for_user(user)
            send_password_reset_email(user.email, user.get_full_name() or user.email, token)
        return Response(
            {'detail': 'Dacă există un cont cu acest email, am trimis un link de resetare.'},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ConfirmResetSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': 'Parola a fost resetată. Te poți conecta acum.'},
            status=status.HTTP_200_OK,
        )

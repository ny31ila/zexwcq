# service-backend/account/views.py
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .serializers import UserRegistrationSerializer, UserProfileSerializer
# from .services import send_sms_otp # Import SMS service function (to be created in util app)
# from .models import PasswordResetOTP # Model to store OTP (to be created)

User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    """View for user registration."""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny] # Anyone can register

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Optionally, log the user in immediately after registration
        # refresh = RefreshToken.for_user(user)
        # return Response({
        #     'user': UserProfileSerializer(user, context=self.get_serializer_context()).data,
        #     'refresh': str(refresh),
        #     'access': str(refresh.access_token),
        # }, status=status.HTTP_201_CREATED)
        return Response(
            {"detail": _("User registered successfully. Please log in.")},
            status=status.HTTP_201_CREATED
        )

class UserProfileView(generics.RetrieveUpdateAPIView):
    """View for retrieving and updating the authenticated user's profile."""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Return the currently authenticated user."""
        return self.request.user

# --- Password Reset Views (Conceptual) ---
# These require additional models and services for OTP management and SMS sending.
# They will be implemented fully later.

# class RequestPasswordResetView(APIView):
#     """View to request a password reset (sends SMS OTP)."""
#     permission_classes = [permissions.AllowAny]
#
#     def post(self, request):
#         # 1. Get phone_number or national_code from request data
#         identifier = request.data.get('identifier') # Could be national_code or phone
#         if not identifier:
#             return Response(
#                 {"detail": _("Identifier (national code or phone number) is required.")},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         # 2. Find user by national_code or phone_number
#         try:
#             user = User.objects.get(
#                 models.Q(national_code=identifier) | models.Q(phone_number=identifier)
#             )
#         except User.DoesNotExist:
#             # For security, it's often better to return a generic message
#             # to avoid leaking information about user existence.
#             return Response(
#                 {"detail": _("If an account exists, an OTP has been sent.")},
#                 status=status.HTTP_200_OK
#             )
#
#         # 3. Generate OTP (implement logic or use a library)
#         # otp_code = generate_otp() # Function to be implemented
#
#         # 4. Save OTP with expiration (requires PasswordResetOTP model)
#         # PasswordResetOTP.objects.create(user=user, otp=otp_code) # Model to be created
#
#         # 5. Send OTP via SMS (requires SMS service)
#         # send_sms_otp(user.phone_number, otp_code) # Service function to be created
#
#         return Response(
#             {"detail": _("If an account exists, an OTP has been sent to your phone number.")},
#             status=status.HTTP_200_OK
#         )

# class ConfirmPasswordResetView(APIView):
#     """View to confirm password reset with OTP and set new password."""
#     permission_classes = [permissions.AllowAny]
#
#     def post(self, request):
#         # 1. Get identifier, otp, new_password, confirm_password from request data
#         identifier = request.data.get('identifier')
#         otp_code = request.data.get('otp')
#         new_password = request.data.get('new_password')
#         confirm_password = request.data.get('confirm_password')
#
#         # 2. Validate input (check if fields are present, passwords match)
#         if not all([identifier, otp_code, new_password, confirm_password]):
#             return Response(
#                 {"detail": _("All fields are required.")},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         if new_password != confirm_password:
#             return Response(
#                 {"detail": _("Passwords do not match.")},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         # 3. Find user
#         try:
#             user = User.objects.get(
#                 models.Q(national_code=identifier) | models.Q(phone_number=identifier)
#             )
#         except User.DoesNotExist:
#             return Response(
#                 {"detail": _("Invalid request.")},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         # 4. Validate OTP (check if exists, not expired, matches)
#         # try:
#         #     otp_record = PasswordResetOTP.objects.get(user=user, otp=otp_code)
#         #     if otp_record.is_expired(): # Method to be implemented on model
#         #         otp_record.delete()
#         #         return Response({"detail": _("OTP has expired.")}, status=status.HTTP_400_BAD_REQUEST)
#         # except PasswordResetOTP.DoesNotExist:
#         #     return Response({"detail": _("Invalid OTP.")}, status=status.HTTP_400_BAD_REQUEST)
#
#         # 5. Set new password
#         user.set_password(new_password)
#         user.save()
#
#         # 6. Delete used OTP record
#         # otp_record.delete()
#
#         return Response(
#             {"detail": _("Password has been reset successfully.")},
#             status=status.HTTP_200_OK
#         )

# --- Logout View (Optional, for blacklisting tokens if configured) ---
# class LogoutView(APIView):
#     permission_classes = (permissions.IsAuthenticated,)
#
#     def post(self, request):
#         try:
#             # If BLACKLIST_AFTER_ROTATION is True in SIMPLE_JWT settings
#             # refresh_token = request.data["refresh_token"]
#             # token = RefreshToken(refresh_token)
#             # token.blacklist()
#             # For now, client just discards tokens.
#             return Response(status=status.HTTP_205_RESET_CONTENT)
#         except Exception as e:
#             return Response(status=status.HTTP_400_BAD_REQUEST)
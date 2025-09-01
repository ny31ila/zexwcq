# service-backend/account/serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'national_code', 'phone_number', 'password', 'password_confirm',
            'first_name', 'last_name', 'gender', 'birth_date_gregorian',
            'birth_date_shamsi', 'email' # profile_picture can be handled separately if needed
        )
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'gender': {'required': False},
            'birth_date_gregorian': {'required': False},
            'birth_date_shamsi': {'required': False},
            'email': {'required': False},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": _("Password fields didn't match.")})
        # You can add more validation here, e.g., checking national_code format
        # or ensuring phone_number uniqueness if not handled by the model constraint.
        return attrs

    def create(self, validated_data):
        # Remove password_confirm as it's not part of the User model
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password) # Hash the password
        user.save()
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for viewing and updating user profile."""
    # Make national_code and phone_number read-only on update if they shouldn't change
    national_code = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'national_code', 'phone_number', 'email',
            'first_name', 'last_name', 'gender',
            'birth_date_gregorian', 'birth_date_shamsi',
            'profile_picture', 'date_joined', 'last_login'
        )
        read_only_fields = ('id', 'date_joined', 'last_login') # These should not be editable

    def validate_email(self, value):
        """Ensure email uniqueness if provided."""
        user = self.context['request'].user
        if value and User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError(_("A user with that email already exists."))
        return value

# Serializers for Password Reset can be added later, likely involving sending SMS.
# They would typically involve:
# 1. A serializer to request reset (takes phone_number/national_code)
# 2. A serializer to confirm reset (takes code, new password, confirm password)
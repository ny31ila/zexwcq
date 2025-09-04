# service-backend/account/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
import jdatetime
from datetime import date

# --- 1. Define a Custom UserManager ---
class CustomUserManager(BaseUserManager):
    """
    Custom manager for the User model where national_code is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, national_code, phone_number, password=None, **extra_fields):
        """
        Create and return a regular User with a national code and phone number.
        """
        if not national_code:
            raise ValueError(_('The National Code must be set'))
        if not phone_number:
            raise ValueError(_('The Phone Number must be set'))
        user = self.model(national_code=national_code, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, national_code, phone_number, password=None, **extra_fields):
        """
        Create and return a SuperUser with a national code and phone number.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(national_code, phone_number, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model for the Nexa platform.
    Uses National Code as the unique username.
    Requires phone number.
    Supports storing birth dates in Gregorian, Jalali (Shamsi), and Hebrew (optional).
    """
    # --- Remove the default username field ---
    username = None

    email = models.EmailField(_("email address"), blank=True, null=True, unique=True)
    national_code = models.CharField(
        _("national code"), max_length=20, unique=True, help_text=_("User's National Code (Unique)")
    )
    # Phone number is required for registration and password reset
    phone_number = models.CharField(
        _("phone number"), max_length=15, unique=True, help_text=_("User's Phone Number (Required)")
    )

    # --- Profile Fields (Updated Mandatory Fields) ---
    # As per agreement, first_name and last_name are mandatory for data integrity,
    # even if not required at initial bulk creation.
    first_name = models.CharField(_("first name"), max_length=150, blank=False) # Mandatory
    last_name = models.CharField(_("last name"), max_length=150, blank=False)  # Mandatory
    GENDER_CHOICES = [
        ('M', _('Male')),
        ('F', _('Female')),
        # ('O', _('Other')), # Add if needed based on prompt
    ]
    gender = models.CharField(_("gender"), max_length=1, choices=GENDER_CHOICES, blank=True)

    # --- Birth Date (Simplified and Gregorian Storage) ---
    # Store the primary date in Gregorian format for database integrity and querying.
    # Conversion to/from Jalali will be handled by serializers/views.
    birth_date = models.DateField(_("birth date (Gregorian)"), blank=True, null=True) # Name simplified

    # Note: birth_date_shamsi field has been removed as per discussion.
    # It can be calculated on-the-fly or stored separately if legacy systems require it,
    # but the primary source is birth_date (Gregorian).

    profile_picture = models.ImageField(_("profile picture"), upload_to='profile_pictures/', blank=True, null=True)

    # --- Use the custom manager ---
    objects = CustomUserManager()

    USERNAME_FIELD = 'national_code'
    REQUIRED_FIELDS = ['phone_number'] # phone_number is required alongside national_code

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return f"{self.national_code} ({self.get_full_name()})"

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.national_code

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.national_code

    def calculate_age(self):
        """Calculate age based on Gregorian birth date."""
        if self.birth_date: # Use the renamed field
            today = date.today()
            return today.year - self.birth_date.year - \
                   ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None

# The Role model and any other models remain the same or are not part of this update...
# If you add a Role model later:
# class Role(models.Model):
#     name = models.CharField(max_length=50, unique=True)
#     def __str__(self):
#         return self.name

# service-backend/assessment/models.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import os

User = settings.AUTH_USER_MODEL

class TestPackage(models.Model):
    """
    Represents a package of assessments that can be purchased by users.
    Packages are filtered based on user age.
    """
    name = models.CharField(_("name"), max_length=255, unique=True)
    description = models.TextField(_("description"), blank=True)
    # --- Currency Change: Store price in Rials ---
    price = models.DecimalField(
        _("price (Rials)"), # Clarify unit in field name/help text
        max_digits=15, # Increased max_digits to accommodate larger Rial values
        decimal_places=0, # Rial is typically a whole number
        default=0,
        help_text=_("Price of the package in Iranian Rials.")
    )
    # --- Age filtering for packages ---
    min_age = models.PositiveIntegerField(_("minimum age"), help_text=_("Minimum age to access this package"))
    max_age = models.PositiveIntegerField(_("maximum age"), help_text=_("Maximum age to access this package"))
    is_active = models.BooleanField(_("is active"), default=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    # --- Relationship: Many Assessments belong to One Package ---
    # This defines the M2M relationship from the Package side.
    # related_name='packages' on Assessment model allows reverse lookup: assessment.packages.all()
    assessments = models.ManyToManyField(
        'Assessment', # Use string name to avoid circular import issues if needed
        related_name='packages', # Access packages from an assessment via assessment.packages.all()
        verbose_name=_("assessments"),
        blank=True, # Allow packages to be created without assessments initially
        help_text=_("The assessments included in this package.")
    )

    class Meta:
        verbose_name = _("Test Package")
        verbose_name_plural = _("Test Packages")
        ordering = ['min_age', 'name']

    def __str__(self):
        return self.name

    def clean(self):
        # You can add validation logic here, e.g., min_age <= max_age
        pass

class Assessment(models.Model):
    """
    Represents a single psychological assessment/test (e.g., Holland, MBTI).
    Questions/answers are stored in structured JSON files.
    Can belong to multiple TestPackages.
    """
    # --- Name and Description ---
    name = models.CharField(_("name"), max_length=100) # e.g., 'Holland', 'MBTI'
    description = models.TextField(_("description"), blank=True)

    # --- JSON File Storage ---
    # Store the path to the JSON file containing questions/answers
    json_filename = models.CharField(
        _("JSON filename"),
        max_length=255,
        help_text=_("Name of the JSON file containing assessment data (e.g., 'holland.json')")
    )

    # --- Status ---
    is_active = models.BooleanField(_("is active"), default=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    # --- NOTE: The M2M relationship is now defined on TestPackage ---
    # The 'packages' related_name is defined on the TestPackage.assessments field.

    class Meta:
        verbose_name = _("Assessment")
        verbose_name_plural = _("Assessments")
        ordering = ['name']

    def __str__(self):
        # Update string representation to reflect the new relationship
        package_names = ", ".join([p.name for p in self.packages.all()])
        return f"{self.name} (in: {package_names})" if package_names else self.name

    def get_json_file_path(self):
        """
        Constructs the full path to the JSON file.
        This assumes files are stored in `assessment/data/` within the app directory.
        """
        from django.apps import apps
        assessment_app_config = apps.get_app_config('assessment')
        app_path = assessment_app_config.path
        return os.path.join(app_path, 'data', self.json_filename)


# UserAssessmentAttempt model remains the same as it links to a specific assessment instance
class UserAssessmentAttempt(models.Model):
    """
    Tracks a user's attempt at completing an assessment.
    Stores start/end times, completion status, and results.
    """
    user = models.ForeignKey(User, related_name='assessment_attempts', on_delete=models.CASCADE, verbose_name=_("user"))
    assessment = models.ForeignKey(Assessment, related_name='user_attempts', on_delete=models.CASCADE, verbose_name=_("assessment"))
    start_time = models.DateTimeField(_("start time"), auto_now_add=True)
    end_time = models.DateTimeField(_("end time"), blank=True, null=True)
    is_completed = models.BooleanField(_("is completed"), default=False)
    raw_results_json = models.JSONField(
        _("raw results JSON"),
        blank=True,
        null=True,
        help_text=_("Raw user answers and initial scoring results.")
    )
    deepseek_input_json = models.JSONField(
        _("deepseek input JSON"),
        blank=True,
        null=True,
        help_text=_("Processed data ready to be sent to the AI service.")
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("User Assessment Attempt")
        verbose_name_plural = _("User Assessment Attempts")
        ordering = ['-start_time']

    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        return f"{self.user} - {self.assessment} ({status})"

    @property
    def duration(self):
        """Calculates the duration of the attempt."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

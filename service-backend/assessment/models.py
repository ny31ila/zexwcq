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
        'Assessment', # Use string name to avoid potential circular import issues
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
    # This path is relative to MEDIA_ROOT or a specific directory within the app
    # Based on our updated blueprint, it's relative to `assessment/data/`
    # We'll store the filename, assuming it's in `assessment/data/`
    json_filename = models.CharField(
        _("JSON filename"),
        max_length=255,
        help_text=_("Name of the JSON file containing assessment data (e.g., 'holland.json')")
    )

    # --- Status ---
    is_active = models.BooleanField(_("is active"), default=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Assessment")
        verbose_name_plural = _("Assessments")
        ordering = ['name']

    def __str__(self):
        # Update string representation to reflect the new relationship
        package_names = ", ".join([p.name for p in self.packages.all()]) # Use related_name 'packages'
        return f"{self.name} (in: {package_names})" if package_names else self.name

    def get_json_file_path(self):
        """
        Constructs the full path to the JSON file.
        This assumes files are stored in `assessment/data/` within the app directory.
        """
        # This gets the path relative to the project root
        from django.apps import apps
        assessment_app_config = apps.get_app_config('assessment')
        app_path = assessment_app_config.path
        return os.path.join(app_path, 'data', self.json_filename)


class UserAssessmentAttempt(models.Model):
    """
    Tracks a user's attempt at completing an assessment.
    Stores start/end times, completion status, and results.
    """
    user = models.ForeignKey(User, related_name='assessment_attempts', on_delete=models.CASCADE, verbose_name=_("user"))
    # --- Link to Assessment, not Package ---
    # The attempt is for a specific assessment instance
    assessment = models.ForeignKey(Assessment, related_name='user_attempts', on_delete=models.CASCADE, verbose_name=_("assessment"))

    start_time = models.DateTimeField(_("start time"), auto_now_add=True)
    end_time = models.DateTimeField(_("end time"), blank=True, null=True)
    is_completed = models.BooleanField(_("is completed"), default=False)

    # --- Updated Comments ---
    # Raw results from the user's answers. Structure depends on the assessment.
    # This field is updated incrementally as the user submits responses.
    raw_results_json = models.JSONField(
        _("raw results JSON"),
        blank=True,
        null=True,
        help_text=_("Raw user answers and initial scoring results, updated incrementally.")
    )

    # --- Renamed Field ---
    # Data formatted specifically for sending to the AI service.
    # This is populated by a background task AFTER the attempt is completed,
    # by processing the data in raw_results_json.
    processed_results_json = models.JSONField( # Renamed from deepseek_input_json
        _("processed results JSON"),
        blank=True,
        null=True,
        help_text=_("Processed/calculated data derived from raw results, ready for AI service.")
    )

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("User Assessment Attempt")
        verbose_name_plural = _("User Assessment Attempts")
        ordering = ['-start_time']
        # Ensure a user can only have one *active/unfinished* attempt per assessment?
        # Or allow multiple attempts? Document requirement is ambiguous.
        # For now, allow multiple attempts.
        # constraints = [
        #     models.UniqueConstraint(
        #         fields=['user', 'assessment', 'is_completed'],
        #         condition=models.Q(is_completed=False),
        #         name='unique_active_attempt_per_user_assessment'
        #     )
        # ]

    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        return f"{self.user} - {self.assessment} ({status})"

    @property
    def duration(self):
        """Calculates the duration of the attempt."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

# Note: AIRecommendation model will be defined in the ai_integration app,
# as it's the result of processing by that service.
# It will likely have a ForeignKey to User.

class AssessmentTestRunner(Assessment):
    """
    A proxy model for running assessment tests in the Django admin.
    This model does not create its own database table. It provides a separate
    entry in the admin interface to trigger and view test results.
    """
    class Meta:
        proxy = True
        verbose_name = _("Assessment Test Runner")
        verbose_name_plural = _("Assessment Test Runners")

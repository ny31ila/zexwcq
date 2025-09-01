# service-backend/assessment/models.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import os

# It's good practice to get the user model dynamically
User = settings.AUTH_USER_MODEL

class TestPackage(models.Model):
    """
    Represents a package of assessments that can be purchased by users.
    Packages are filtered based on user age.
    """
    name = models.CharField(_("name"), max_length=255, unique=True)
    description = models.TextField(_("description"), blank=True)
    price = models.DecimalField(_("price"), max_digits=10, decimal_places=2, default=0.00)
    # Age filtering for packages
    min_age = models.PositiveIntegerField(_("minimum age"), help_text=_("Minimum age to access this package"))
    max_age = models.PositiveIntegerField(_("maximum age"), help_text=_("Maximum age to access this package"))
    is_active = models.BooleanField(_("is active"), default=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

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
    """
    package = models.ForeignKey(TestPackage, related_name='assessments', on_delete=models.CASCADE, verbose_name=_("package"))
    name = models.CharField(_("name"), max_length=100) # e.g., 'Holland', 'MBTI'
    description = models.TextField(_("description"), blank=True)
    # Store the path to the JSON file containing questions/answers
    # This path is relative to MEDIA_ROOT or a specific directory within the app
    # Based on our updated blueprint, it's relative to `assessment/data/`
    # We'll store the filename, assuming it's in `assessment/data/`
    json_filename = models.CharField(
        _("JSON filename"),
        max_length=255,
        help_text=_("Name of the JSON file containing assessment data (e.g., 'holland.json')")
    )
    is_active = models.BooleanField(_("is active"), default=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Assessment")
        verbose_name_plural = _("Assessments")
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (in {self.package.name})"

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

    # Consider adding a method to load and parse the JSON data if frequently accessed
    # def load_json_data(self):
    #     import json
    #     try:
    #         with open(self.get_json_file_path(), 'r', encoding='utf-8') as f:
    #             return json.load(f)
    #     except FileNotFoundError:
    #         # Handle error appropriately
    #         return None
    #     except json.JSONDecodeError:
    #         # Handle error appropriately
    #         return None


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

    # Raw results from the user's answers. Structure depends on the assessment.
    raw_results_json = models.JSONField(
        _("raw results JSON"),
        blank=True,
        null=True,
        help_text=_("Raw user answers and initial scoring results.")
    )

    # Data formatted specifically for sending to the AI service.
    # This might be a processed version of raw_results_json.
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
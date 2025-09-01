# service-backend/career/models.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

# It's good practice to get the user model dynamically
User = settings.AUTH_USER_MODEL

class JobOpening(models.Model):
    """
    Represents a job opportunity listed in the Job Market module.
    """
    title = models.CharField(_("title"), max_length=255)
    company = models.CharField(_("company"), max_length=255)
    location = models.CharField(_("location"), max_length=255, blank=True)
    description = models.TextField(_("description"))
    requirements = models.TextField(_("requirements"), blank=True)
    # URL to the original job posting or application page
    url = models.URLField(_("external URL"), max_length=500, blank=True, null=True)
    # Link to the user (admin/content manager) who posted it
    # Note: Using settings.AUTH_USER_MODEL directly for ForeignKey can cause issues during migrations
    # if the model is swappable. Using a string reference is safer.
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='job_postings',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("posted by")
    )
    is_active = models.BooleanField(_("is active"), default=True)
    posted_at = models.DateTimeField(_("posted at"), auto_now_add=True)
    # Optional: Add fields like application deadline, salary range, job type (Full-time, Part-time), etc.
    # application_deadline = models.DateField(_("application deadline"), blank=True, null=True)
    # salary_range = models.CharField(_("salary range"), max_length=100, blank=True)

    class Meta:
        verbose_name = _("Job Opening")
        verbose_name_plural = _("Job Openings")
        ordering = ['-posted_at']

    def __str__(self):
        return f"{self.title} at {self.company}"


class BusinessResource(models.Model):
    """
    Represents resources and information for starting/running a business.
    """
    RESOURCE_TYPES = [
        ('law', _('Law')),
        ('advice', _('Advice')),
        ('template', _('Template')),
        ('funding', _('Funding')),
        ('training', _('Training')),
        # Add more types as needed
    ]

    title = models.CharField(_("title"), max_length=255)
    description = models.TextField(_("description"))
    # URL to the resource (could be internal or external)
    url = models.URLField(_("URL"), max_length=500)
    resource_type = models.CharField(_("resource type"), max_length=20, choices=RESOURCE_TYPES)
    # Link to the user (admin/content manager) who added it
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='business_resources_added',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("added by")
    )
    is_active = models.BooleanField(_("is active"), default=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    # Optional: Add fields like target audience (startup, established business), language, etc.

    class Meta:
        verbose_name = _("Business Resource")
        verbose_name_plural = _("Business Resources")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_resource_type_display()})"

# Note: The prompt mentions "تعامل با مشاوران" (interaction with consultants).
# This likely involves linking to the `Consultant` model (which will be in the `counseling` app)
# or allowing users to submit questions/messages.
# A separate model like `BusinessConsultationRequest` might be needed in this or the `counseling` app.
# For now, we'll keep the models focused on job openings and resources.

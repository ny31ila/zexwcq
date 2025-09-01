# service-backend/resume/models.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid
import os

User = settings.AUTH_USER_MODEL

def resume_pdf_upload_path(instance, filename):
    """Generate upload path for resume PDF files."""
    # File will be uploaded to MEDIA_ROOT/resumes/pdfs/user_<id>/<filename>
    return f'resumes/pdfs/user_{instance.user.id}/{filename}'

class Resume(models.Model):
    """
    Stores user-generated resumes.
    Includes template selection, data, and generated PDF/link.
    """
    TEMPLATE_CHOICES = [
        ('classic', _('Classic')),
        ('modern', _('Modern')),
        ('minimal', _('Minimal')),
        # Add more templates as needed
    ]

    user = models.ForeignKey(User, related_name='resumes', on_delete=models.CASCADE, verbose_name=_("user"))
    title = models.CharField(_("title"), max_length=255, default=_("My Resume")) # Allow user to name their resume

    # Template selection
    template_type = models.CharField(
        _("template type"), max_length=20, choices=TEMPLATE_CHOICES, default='classic'
    )

    # Store all resume data in a structured JSON field.
    # This includes pre-filled data from the user profile and user-edited fields.
    data_json = models.JSONField(
        _("resume data JSON"),
        help_text=_("Structured data for the resume content (personal info, education, experience, etc.)")
    )

    # Generated PDF file
    generated_pdf = models.FileField(
        _("generated PDF"), upload_to=resume_pdf_upload_path, blank=True, null=True
    )
    # Note: Consider using FileField instead of URLField if the file is stored locally.
    # If using an external storage service, URLField might be appropriate.

    # Shareable link token
    shareable_link_token = models.UUIDField(
        _("shareable link token"), default=uuid.uuid4, unique=True, editable=False
    )

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Resume")
        verbose_name_plural = _("Resumes")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.get_full_name()}"

    def get_shareable_link(self):
        """
        Generates the full shareable link URL.
        Requires the domain/base URL to be configured.
        This is a placeholder; actual URL generation should happen in views/serializers.
        """
        # Example: return f"https://yourdomain.com/api/resumes/share/{self.shareable_link_token}/"
        # Or use Django's reverse and request.build_absolute_uri in the view
        return f"/api/resumes/share/{self.shareable_link_token}/" # Relative path placeholder

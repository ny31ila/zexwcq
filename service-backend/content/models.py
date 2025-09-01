# service-backend/content/models.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

User = settings.AUTH_USER_MODEL

class NewsArticle(models.Model):
    """
    Represents a news article or announcement published on the platform.
    """
    title = models.CharField(_("title"), max_length=255)
    content = models.TextField(_("content"))
    # Link to the user (admin/content manager) who authored it
    author = models.ForeignKey(
        User,
        related_name='authored_news',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("author")
    )
    published_at = models.DateTimeField(_("published at"), null=True, blank=True)
    is_published = models.BooleanField(_("is published"), default=False)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    # Optional: Add fields like slug, tags, summary, image, etc.

    class Meta:
        verbose_name = _("News Article")
        verbose_name_plural = _("News Articles")
        ordering = ['-published_at', '-created_at'] # Show newest published first

    def __str__(self):
        status = _("Published") if self.is_published and self.published_at else _("Draft")
        return f"{self.title} ({status})"

    @property
    def is_draft(self):
        """Check if the article is a draft."""
        return not (self.is_published and self.published_at)

# If you need other general content types in the future, you can add them here.
# For example, a simple 'Page' model for 'About Us' or 'Contact Us' if content is dynamic:
#
# class Page(models.Model):
#     """
#     Represents a static page like 'About Us' or 'Contact Us'.
#     Content can be managed via the admin panel.
#     """
#     SLUG_CHOICES = [
#         ('about', 'About Us'),
#         ('contact', 'Contact Us'),
#         # Add more as needed
#     ]
#     slug = models.SlugField(_("slug"), unique=True, choices=SLUG_CHOICES)
#     title = models.CharField(_("title"), max_length=255)
#     content = models.TextField(_("content"))
#     created_at = models.DateTimeField(_("created at"), auto_now_add=True)
#     updated_at = models.DateTimeField(_("updated at"), auto_now=True)
#
#     class Meta:
#         verbose_name = _("Page")
#         verbose_name_plural = _("Pages")
#
#     def __str__(self):
#         return self.title

# For a 'Contact Us' form submission, you might have a model like this:
# (Note: The prompt says 'فرم ارسال پیام', which implies storing messages)
#
# class ContactMessage(models.Model):
#     """
#     Stores messages submitted via the 'Contact Us' form.
#     """
#     name = models.CharField(_("name"), max_length=100)
#     email = models.EmailField(_("email"))
#     subject = models.CharField(_("subject"), max_length=200)
#     message = models.TextField(_("message"))
#     submitted_at = models.DateTimeField(_("submitted at"), auto_now_add=True)
#     # Optional: Add a field to mark as read/processed
#     is_processed = models.BooleanField(_("is processed"), default=False)
#
#     class Meta:
#         verbose_name = _("Contact Message")
#         verbose_name_plural = _("Contact Messages")
#         ordering = ['-submitted_at']
#
#     def __str__(self):
#         return f"Message from {self.name} - {self.subject}"

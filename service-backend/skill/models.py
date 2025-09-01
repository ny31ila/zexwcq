# service-backend/skill/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class SkillCategory(models.Model):
    """
    Represents a category for grouping courses or resources.
    E.g., 'Programming', 'Design', 'Business Skills'.
    """
    name = models.CharField(_("name"), max_length=100, unique=True)
    description = models.TextField(_("description"), blank=True)
    # Optional: Add fields for icon, color, order, etc.

    class Meta:
        verbose_name = _("Skill Category")
        verbose_name_plural = _("Skill Categories")
        ordering = ['name']

    def __str__(self):
        return self.name

class Course(models.Model):
    """
    Represents a course or resource for skill enhancement.
    Can be recommended by AI or manually curated.
    """
    title = models.CharField(_("title"), max_length=255)
    description = models.TextField(_("description"), blank=True)
    url = models.URLField(_("URL"), max_length=500, help_text=_("Link to the course/resource"))
    
    category = models.ForeignKey(
        SkillCategory,
        related_name='courses',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("category")
    )
    
    # Flag to indicate if this course was recommended by the AI
    recommended_by_ai = models.BooleanField(
        _("recommended by AI"), default=False,
        help_text=_("Indicates if this course was suggested by the AI analysis.")
    )
    
    # Optional: Add fields like duration, difficulty level, provider, etc.
    # duration = models.DurationField(_("duration"), blank=True, null=True)
    # difficulty = models.CharField(_("difficulty"), max_length=20, choices=[('Beginner', 'Beginner'), ('Intermediate', 'Intermediate'), ('Advanced', 'Advanced')], blank=True)
    # provider = models.CharField(_("provider"), max_length=100, blank=True) # e.g., 'Coursera', 'Udemy'

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Course")
        verbose_name_plural = _("Courses")
        ordering = ['-created_at']

    def __str__(self):
        category_name = self.category.name if self.category else "Uncategorized"
        return f"{self.title} ({category_name})"

# Note: If resources are distinct from courses (e.g., articles, videos),
# you might consider a separate 'Resource' model or a 'content_type' field in Course.
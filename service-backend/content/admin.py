# service-backend/content/admin.py
from django.contrib import admin
from .models import NewsArticle

@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'is_published', 'published_at', 'created_at')
    list_filter = ('is_published', 'published_at', 'created_at')
    search_fields = ('title', 'content')
    readonly_fields = ('created_at', 'updated_at')
    # raw_id_fields = ('author',) # Useful for large user sets
    # Add a filter for published/draft if needed
    # def get_list_filter(self, request):
    #     return super().get_list_filter(request) + ('is_published',)

# If you add the Page or ContactMessage models later:
# @admin.register(Page)
# class PageAdmin(admin.ModelAdmin):
#     list_display = ('title', 'slug', 'updated_at')
#     prepopulated_fields = {"slug": ("title",)} # Auto-fill slug from title
#     readonly_fields = ('created_at', 'updated_at')

# @admin.register(ContactMessage)
# class ContactMessageAdmin(admin.ModelAdmin):
#     list_display = ('name', 'email', 'subject', 'submitted_at', 'is_processed')
#     list_filter = ('submitted_at', 'is_processed')
#     search_fields = ('name', 'email', 'subject', 'message')
#     readonly_fields = ('name', 'email', 'subject', 'message', 'submitted_at')

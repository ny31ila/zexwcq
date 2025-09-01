# service-backend/content/serializers.py
from rest_framework import serializers
from .models import NewsArticle

class NewsArticleSerializer(serializers.ModelSerializer):
    """Serializer for NewsArticle model."""
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = NewsArticle
        fields = ('id', 'title', 'content', 'author_name', 'published_at', 'is_published')
        read_only_fields = ('id', 'author_name', 'published_at', 'is_published')

    def get_author_name(self, obj):
        if obj.author:
            return f"{obj.author.first_name} {obj.author.last_name}".strip() or obj.author.national_code
        return None

# If you add a Page model:
# class PageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Page
#         fields = '__all__' # Or specify fields

# If you add a ContactMessage model and want users to submit messages via API:
# class ContactMessageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ContactMessage
#         fields = ('name', 'email', 'subject', 'message')
#         # All fields are required for submission

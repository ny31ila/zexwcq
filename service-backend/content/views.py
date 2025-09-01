# service-backend/content/views.py
from rest_framework import generics, permissions, filters, status, views
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
# Import your models and serializers
from .models import NewsArticle
from .serializers import NewsArticleSerializer

# For publicly accessible content like news
class NewsArticleListView(generics.ListAPIView):
    """
    List all published news articles.
    Publicly accessible.
    """
    queryset = NewsArticle.objects.filter(is_published=True).order_by('-published_at')
    serializer_class = NewsArticleSerializer
    permission_classes = [permissions.AllowAny] # Public endpoint
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content']
    ordering_fields = ['published_at', 'title']
    ordering = ['-published_at']

class NewsArticleDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of a specific published news article.
    Publicly accessible.
    """
    queryset = NewsArticle.objects.filter(is_published=True)
    serializer_class = NewsArticleSerializer
    permission_classes = [permissions.AllowAny] # Public endpoint
    lookup_field = 'id'

# If you add a Page model for dynamic 'About Us'/'Contact Us':
# class PageDetailView(generics.RetrieveAPIView):
#     queryset = Page.objects.all()
#     serializer_class = PageSerializer
#     permission_classes = [permissions.AllowAny] # Public endpoint
#     lookup_field = 'slug' # Use slug to find the page

# If you add a ContactMessage model:
# from .models import ContactMessage
# from .serializers import ContactMessageSerializer
#
# class ContactUsView(views.APIView):
#     """
#     Submit a message via the 'Contact Us' form.
#     Publicly accessible.
#     """
#     permission_classes = [permissions.AllowAny] # Public endpoint
#
#     def post(self, request, *args, **kwargs):
#         serializer = ContactMessageSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save() # Save the message to the database
#             # Optionally, send an email notification to admins here
#             # Or trigger a Celery task to send email
#             return Response(
#                 {"detail": _("Your message has been sent successfully.")},
#                 status=status.HTTP_201_CREATED
#             )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

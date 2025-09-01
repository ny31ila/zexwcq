# service-backend/career/views.py
from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
# Import your models and serializers
from .models import JobOpening, BusinessResource
from .serializers import JobOpeningSerializer, BusinessResourceSerializer

class JobOpeningListView(generics.ListAPIView):
    """
    List all active job openings.
    """
    queryset = JobOpening.objects.filter(is_active=True)
    serializer_class = JobOpeningSerializer
    permission_classes = [permissions.IsAuthenticated] # Or AllowAny if public listings are desired
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['title', 'company', 'location', 'description', 'requirements']
    filterset_fields = ['location'] # Add more filters as needed (e.g., company)
    ordering_fields = ['posted_at', 'title', 'company']
    ordering = ['-posted_at']

class JobOpeningDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of a specific job opening.
    """
    queryset = JobOpening.objects.filter(is_active=True)
    serializer_class = JobOpeningSerializer
    permission_classes = [permissions.IsAuthenticated] # Or AllowAny
    lookup_field = 'id'

class BusinessResourceListView(generics.ListAPIView):
    """
    List all active business resources.
    """
    queryset = BusinessResource.objects.filter(is_active=True)
    serializer_class = BusinessResourceSerializer
    permission_classes = [permissions.IsAuthenticated] # Or AllowAny
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['title', 'description']
    filterset_fields = ['resource_type'] # Allow filtering by type
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']

class BusinessResourceDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of a specific business resource.
    """
    queryset = BusinessResource.objects.filter(is_active=True)
    serializer_class = BusinessResourceSerializer
    permission_classes = [permissions.IsAuthenticated] # Or AllowAny
    lookup_field = 'id'

# If a feature for users to ask business consultants is added later,
# views for submitting and listing those requests would go here.
# Example:
# class AskBusinessConsultantView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#
#     def post(self, request, *args, **kwargs):
#         serializer = AskBusinessConsultantSerializer(data=request.data)
#         if serializer.is_valid():
#             # Process the request (e.g., save to a model, send email, notify a consultant group)
#             # This would likely involve creating a model instance and possibly triggering a task
#             # from .tasks import process_business_consultation_request
#             # process_business_consultation_request.delay(request.user.id, serializer.validated_data)
#             return Response(
#                 {"detail": _("Your request has been submitted.")},
#                 status=status.HTTP_201_CREATED
#             )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

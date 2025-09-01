# service-backend/resume/views.py
from rest_framework import generics, status, permissions, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404
# Import your models and serializers
from .models import Resume
from .serializers import (
    ResumeCreateUpdateSerializer, ResumeDetailSerializer,
    ResumeListSerializer, GeneratePDFSerializer, GeneratePDFResponseSerializer
)
# Import user model
from django.conf import settings
User = settings.AUTH_USER_MODEL

class ResumeListView(generics.ListAPIView):
    """
    List all resumes for the authenticated user.
    """
    serializer_class = ResumeListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']
    search_fields = ['title']

    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)

class ResumeCreateView(generics.CreateAPIView):
    """
    Create a new resume for the authenticated user.
    """
    serializer_class = ResumeCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    # The serializer's create method handles associating the user

class ResumeDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of a specific resume for the authenticated user.
    """
    serializer_class = ResumeDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)

class ResumeUpdateView(generics.UpdateAPIView):
    """
    Update an existing resume for the authenticated user.
    """
    serializer_class = ResumeCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)

class ResumeDeleteView(generics.DestroyAPIView):
    """
    Delete a resume for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)

class GeneratePDFView(APIView):
    """
    Trigger the generation of a PDF for a specific resume.
    This view initiates a background task (e.g., via Celery).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, resume_id, *args, **kwargs):
        # 1. Get the resume instance (ensure it belongs to the user)
        resume = get_object_or_404(Resume, id=resume_id, user=request.user)

        # 2. Trigger the PDF generation task
        # This requires Celery to be set up.
        # from .tasks import generate_resume_pdf # Import the Celery task
        # task = generate_resume_pdf.delay(resume.id) # Call the task asynchronously

        # 3. Return a response
        # Option 1: Just acknowledge the request
        # return Response(
        #     {"detail": _("PDF generation started.")},
        #     status=status.HTTP_202_ACCEPTED
        # )

        # Option 2: Return task ID for status checking (requires Celery result backend)
        # return Response(
        #     {
        #         "detail": _("PDF generation started."),
        #         "task_id": task.id # Return the Celery task ID
        #     },
        #     status=status.HTTP_202_ACCEPTED
        # )

        # For now, without Celery fully integrated, we'll just acknowledge.
        # In practice, you'd call the task here.
        # Placeholder response
        return Response(
            {"detail": _("PDF generation functionality will be implemented with Celery.")},
            status=status.HTTP_202_ACCEPTED
        )

# View for accessing the shareable link (Public access, no auth required for the link itself)
class ShareableResumeView(APIView):
    """
    View a resume via its shareable link token.
    This endpoint is publicly accessible via the unique token.
    """
    permission_classes = [permissions.AllowAny] # No authentication needed for shared link

    def get(self, request, token, *args, **kwargs):
        # 1. Find the resume by the token
        resume = get_object_or_404(Resume, shareable_link_token=token)

        # 2. Check if a PDF exists
        if resume.generated_pdf:
            # 2a. If PDF exists, serve it
            # Important: Ensure file access is secure and files are not executable.
            pdf_file_path = resume.generated_pdf.path
            if os.path.exists(pdf_file_path):
                with open(pdf_file_path, 'rb') as pdf_file:
                    response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                    # Optionally suggest a filename for download
                    response['Content-Disposition'] = f'inline; filename="{resume.title}.pdf"'
                    return response
            else:
                # PDF file path exists in DB but file is missing on disk
                return Response(
                    {"detail": _("PDF file not found on server.")},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # 2b. If no PDF, return the data_json or a message
            # Returning data_json might not be ideal for a public link,
            # perhaps redirect to a web page that renders it, or return HTML.
            # For API, returning data_json is one option.
            # serializer = ResumeDetailSerializer(resume, context={'request': request})
            # return Response(serializer.data)

            # Simpler response for now
            return Response(
                {
                    "detail": _("Resume PDF is not yet generated."),
                    "title": resume.title,
                    # "data": resume.data_json # Be cautious about exposing raw data publicly
                },
                status=status.HTTP_404_NOT_FOUND # Or 200 with a different message
            )

        # If resume not found by token, get_object_or_404 raises Http404

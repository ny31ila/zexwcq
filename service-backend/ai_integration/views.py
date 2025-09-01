# service-backend/ai_integration/views.py
from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import AIRecommendation
from .serializers import AIRecommendationSerializer

# Assuming the user can only see their own recommendations
class UserAIRecommendationListView(generics.ListAPIView):
    """
    List all AI recommendations for the authenticated user.
    """
    serializer_class = AIRecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['timestamp', 'recommendation_type']
    ordering = ['-timestamp']
    filterset_fields = ['recommendation_type'] # Allow filtering by type

    def get_queryset(self):
        return AIRecommendation.objects.filter(user=self.request.user)

# If you need a detail view for a specific recommendation
class UserAIRecommendationDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of a specific AI recommendation for the authenticated user.
    """
    serializer_class = AIRecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return AIRecommendation.objects.filter(user=self.request.user)

# Views for triggering AI processing or checking status would go here.
# These would likely interact with Celery tasks.
# For example:
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from .tasks import trigger_ai_analysis_for_user # Hypothetical task

# class TriggerAIAnalysisView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#
#     def post(self, request, *args, **kwargs):
#         # Trigger the Celery task
#         task_id = trigger_ai_analysis_for_user.delay(request.user.id)
#         return Response(
#             {"detail": "AI analysis triggered.", "task_id": task_id},
#             status=status.HTTP_202_ACCEPTED
#         )

# class AIAnalysisStatusView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#
#     def get(self, request, task_id, *args, **kwargs):
#         # Check the status of the Celery task
#         # This requires Celery result backend to be configured
#         from celery.result import AsyncResult
#         res = AsyncResult(task_id) # task_id would come from URL or request
#
#         if res.state == 'PENDING':
#             response = {'state': res.state, 'status': 'Task is waiting to be processed.'}
#         elif res.state == 'PROGRESS':
#             response = {
#                 'state': res.state,
#                 'current': res.info.get('current', 0),
#                 'total': res.info.get('total', 1),
#                 'status': res.info.get('status', '')
#             }
#         elif res.state == 'SUCCESS':
#             response = {'state': res.state, 'result': res.info}
#         else:
#             # something went wrong in the background job
#             response = {'state': res.state, 'error': str(res.info)} # res.info might contain the exception
#
#         return Response(response)

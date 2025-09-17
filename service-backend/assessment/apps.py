# service-backend/assessment/apps.py
from django.apps import AppConfig

class AssessmentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'assessment'



# 7 assessments with 509 questions.   disc (24), gardner (80), holland (227), mbti (60), neo (60), pvq (40), swanson (18)
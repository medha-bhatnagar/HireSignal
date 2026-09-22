from django.urls import path
from .views import analyze_profile, match_job

urlpatterns = [
    path("analyze/<str:username>/", analyze_profile),
    path("match/<str:username>/", match_job),
]
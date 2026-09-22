from django.urls import path

from .views import github_callback, refresh_token

urlpatterns = [
    path("github/callback/", github_callback),
    path("refresh/", refresh_token),
]

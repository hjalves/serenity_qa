"""serenity_qa URL Configuration
"""

from django.contrib import admin
from django.urls import path

from questions import views

urlpatterns = [
    path("", views.IndexView.as_view(), name='index'),
    path("video/<int:video>/", views.VideoView.as_view(), name='video'),
    path("admin/", admin.site.urls),
]

"""serenity_qa URL Configuration
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from .apps.questions import views
from .components.question_list import views as question_list_views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("video/<int:video>/", views.VideoView.as_view(), name="video"),
    path(
        "admin/htmx/video/<int:video>/questions/",
        question_list_views.QuestionListView.as_view(),
        name="question-list",
    ),
    path(
        "admin/htmx/video/<int:video>/questions/<int:question>/",
        question_list_views.QuestionDetailView.as_view(),
        name="question-list-detail",
    ),
    path("admin/", admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

"""serenity_qa URL Configuration
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from .apps.questions import views as questions_views
from .apps.cms import views as cms_views
from .components.question_list import views as question_list_views

urlpatterns = [
    path("", cms_views.IndexView.as_view(), name="index"),
    path("<slug:page>/", cms_views.PageView.as_view(), name="page"),
    path("video/<int:video>/", questions_views.VideoView.as_view(), name="video"),
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

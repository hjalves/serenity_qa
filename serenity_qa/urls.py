"""serenity_qa URL Configuration
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from .questions import views as questions_views
from serenity_qa.cms import views as cms_views
from .components.question_list import views as question_list_views

urlpatterns = [
    path("", cms_views.PageView.as_view(), name="index"),
    path("tags.css", questions_views.TagsCSSView.as_view(), name="tagcss"),
    path("videos/<int:video>/", questions_views.VideoView.as_view(), name="video"),
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
    path("<slug:page>/", cms_views.PageView.as_view(), name="page"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

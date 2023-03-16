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
    path("search/", questions_views.SearchView.as_view(), name="search"),
    path("tags/", questions_views.TagListView.as_view(), name="tag-list"),
    path("tags/<slug:slug>/", questions_views.TagDetailView.as_view(), name="tag-detail"),
    path("videos/", questions_views.VideoListView.as_view(), name="video-list"),
    path(
        "videos/<video>/", questions_views.VideoDetailView.as_view(), name="video-detail"
    ),
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

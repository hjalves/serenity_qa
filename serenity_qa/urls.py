"""serenity_qa URL Configuration
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from questions import views

urlpatterns = [
    path("", views.IndexView.as_view(), name='index'),
    path("video/<int:video>/", views.VideoView.as_view(), name='video'),
    path("admin/htmx/video/<int:video>/questions/", views.HtmxQuestionListView.as_view()),
    path("admin/htmx/video/<int:video>/questions/<int:question>/", views.HtmxQuestionDetailView.as_view()),
    path("admin/", admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

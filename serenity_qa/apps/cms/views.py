from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from serenity_qa.apps.cms.models import Page
from serenity_qa.apps.questions.models import Video


class IndexView(TemplateView):
    template_name = "cms/index.html"

    def get_context_data(self, **kwargs):
        kw = super().get_context_data(**kwargs)
        kw["videos"] = Video.objects.all()
        return kw


class PageView(TemplateView):
    template_name = "cms/page.html"

    def get_context_data(self, page=None, **kwargs):
        context = super().get_context_data(**kwargs)
        page = get_object_or_404(Page.objects.published(), slug=page)
        context["self"] = context["page"] = page
        return context

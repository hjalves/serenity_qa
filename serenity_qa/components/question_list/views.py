from django.http import HttpResponse
from django.http import QueryDict
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from serenity_qa.questions.forms import VideoQuestionForm
from serenity_qa.questions.models import Video


class QuestionListView(TemplateView):
    template_name = "question_list/partials/question_list.html"

    def get_context_data(self, **kwargs):
        video = get_object_or_404(Video, id=kwargs["video"])
        context = super().get_context_data(**kwargs)
        context["form"] = VideoQuestionForm()
        context["video"] = video
        return context

    def post(self, request, *args, **kwargs):
        video = get_object_or_404(Video, id=kwargs["video"])
        form = VideoQuestionForm(request.POST)
        if form.is_valid():
            question = video.question_set.create(**form.cleaned_data)
            kwargs["editing_question"] = question
            return self.get(request, *args, **kwargs)
        return HttpResponse("", status=204)


class QuestionDetailView(TemplateView):
    template_name = "question_list/partials/question_detail.html"

    def get_context_data(self, **kwargs):
        video = get_object_or_404(Video, id=kwargs["video"])
        question = get_object_or_404(video.question_set, id=kwargs["question"])
        context = super().get_context_data(**kwargs)
        context["video"] = video
        context["question"] = question
        if "edit" in self.request.GET:
            context["edit"] = True
        return context

    def patch(self, request, *args, **kwargs):
        data = QueryDict(request.body)
        video = get_object_or_404(Video, id=kwargs["video"])
        question = get_object_or_404(video.question_set, id=kwargs["question"])
        question.question = data["question"]
        question.save()
        return self.get(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        video = get_object_or_404(Video, id=kwargs["video"])
        question = get_object_or_404(video.question_set, id=kwargs["question"])
        question.delete()
        return HttpResponse("", status=200)

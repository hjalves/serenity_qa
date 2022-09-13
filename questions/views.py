from django.http import HttpResponse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import TemplateView

from questions.forms import VideoQuestionForm
from questions.models import Video


def home(request):
    return HttpResponse('<h1>Page was found</h1>')


class IndexView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        kw = super().get_context_data(**kwargs)
        kw['videos'] = Video.objects.all()
        return kw


class VideoView(TemplateView):
    template_name = 'video.html'

    def get_context_data(self, **kwargs):
        video_id = kwargs['video']
        video = get_object_or_404(Video, id=video_id)
        kw = super().get_context_data(**kwargs)
        kw['videos'] = Video.objects.all()
        kw['questions'] = video.question_set.order_by('timestamp')
        return kw


class HtmxQuestionListView(TemplateView):
    template_name = 'admin/questions/video/question_list_partial.html'

    def get_context_data(self, **kwargs):
        video = get_object_or_404(Video, id=kwargs['video'])
        context = super().get_context_data(**kwargs)
        context['form'] = VideoQuestionForm()
        context['video'] = video
        return context

    def post(self, request, *args, **kwargs):
        video = get_object_or_404(Video, id=kwargs['video'])
        form = VideoQuestionForm(request.POST)
        if form.is_valid():
            question = video.question_set.create(**form.cleaned_data)
            return self.get(request, *args, **kwargs)
        else:
            print(form.errors)
        return HttpResponse("", status=204)


class HtmxQuestionDetailView(View):
    def delete(self, request, *args, **kwargs):
        video = get_object_or_404(Video, id=kwargs['video'])
        question = get_object_or_404(video.question_set, id=kwargs['question'])
        question.delete()
        return HttpResponse("", status=200)

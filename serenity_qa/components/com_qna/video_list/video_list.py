from django.db.models import Sum, Count
from django_components import component

from serenity_qa.questions.models import Video


@component.register("video_list")
class VideoListComponent(component.Component):
    template_name = "com_qna/video_list/video_list.html"

    class Media:
        css = "com_qna/video_list/video_list.css"
        js = None

    def get_context_data(self):
        videos = list(
            Video.objects.all()
            .filter(question__isnull=False)
            .annotate(Count("question"))
            .order_by("-published")
        )
        video_count = len(videos)
        question_count = sum(v.question_count() for v in videos)

        return {
            "videos": videos,
            "video_count": video_count,
            "question_count": question_count,
        }

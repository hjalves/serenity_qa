from django_components import component


@component.register("video_info")
class VideoInfoComponent(component.Component):
    template_name = "com_qna/video_info/video_info.html"

    class Media:
        css = "com_qna/video_info/video_info.css"
        js = None

    def get_context_data(self, **kw):
        context = {}
        video = kw.get("video")
        if video:
            context["id"] = "video_info"
            context["emoji"] = video.emoji
            context["title"] = video.title
            context["url"] = video.url
            context["duration"] = video.duration
            context["published"] = video.published
            context["questions"] = video.question_count()
        return context

from django_components import component


@component.register("metadata")
class MetadataComponent(component.Component):
    template_name = "com_qna/metadata/metadata.html"

    class Media:
        css = "com_qna/metadata/metadata.css"
        js = None

    def get_context_data(self, **kw):
        context = {}
        video = kw.get("video")
        if video:
            context["id"] = "metadata"
            context["emoji"] = video.emoji
            context["title"] = video.title
            context["url"] = video.url
            context["duration"] = video.duration
            context["published"] = video.published
            context["questions"] = video.question_count()
        return context

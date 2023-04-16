from django_components import component


@component.register("tag_info")
class TagInfoComponent(component.Component):
    template_name = "com_qna/tag_info/tag_info.html"

    class Media:
        css = "com_qna/tag_info/tag_info.css"
        js = None

    def get_context_data(self, **kw):
        context = {}
        tag = kw.get("tag")
        if tag:
            context["id"] = "tag_info"
            context["emoji"] = tag.emoji
            context["name"] = tag.name
            context["description"] = tag.description
            context["questions"] = tag.question_count()
            context["duration"] = tag.total_duration()
        return context

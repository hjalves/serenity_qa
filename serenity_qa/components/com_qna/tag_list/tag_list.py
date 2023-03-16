from django_components import component

from serenity_qa.questions.models import Tag


@component.register("tag_list")
class TagListComponent(component.Component):
    template_name = "com_qna/tag_list/tag_list.html"

    class Media:
        css = "com_qna/tag_list/tag_list.css"
        js = None

    def get_context_data(self):
        tags = Tag.objects.all()
        tag_count = tags.count()
        return {"tags": tags, "tag_count": tag_count}

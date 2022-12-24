from django_components import component


@component.register("question")
class QuestionList(component.Component):
    template_name = "question/question.html"

    # noinspection PyMethodOverriding
    def get_context_data(self, question, id=None):
        return {"question": question, "id": id or question.element_id}

    class Media:
        css = "question/question.css"
        js = None

from django_components import component

from serenity_qa.apps.questions.models import Question


@component.register("question")
class QuestionComponent(component.Component):
    template_name = "question/question.html"

    def get_context_data(self, question=None, id=None, arguments=None):
        if arguments:
            question_id = arguments.get("question")
            try:
                question = Question.objects.get(id=question_id)
            except Question.DoesNotExist:
                question = None
        return {"question": question, "id": id or (question and question.element_id)}

    class Media:
        css = "question/question.css"
        js = None

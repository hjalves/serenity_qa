from django_components import component


@component.register("question_list")
class QuestionList(component.Component):
    template_name = "question_list/question_list.html"

    # noinspection PyMethodOverriding
    def get_context_data(self, id, video):
        return {
            "id": id,
            "video": video,
        }

    class Media:
        css = "question_list/question_list.css"
        js = "question_list/question_list.js"

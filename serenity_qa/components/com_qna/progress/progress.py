from django_components import component

from serenity_qa.questions.models import ProgressReport


@component.register("progress")
class ProgressComponent(component.Component):
    template_name = "com_qna/progress/progress.html"

    class Media:
        css = "com_qna/progress/progress.css"
        js = None

    def get_context_data(self, id=None, arguments=None):
        if arguments and "id" in arguments:
            id = arguments["id"]

        try:
            report = ProgressReport.objects.latest()
        except ProgressReport.DoesNotExist:
            indicators = {}
            last_changed = None
        else:
            indicators = report.indicators
            last_changed = report.created_on

        return {
            "id": id or "",
            "last_changed": last_changed,
            **indicators,
        }

from django_components import component

from serenity_qa.questions.models import ProgressReport


@component.register("progress")
class ProgressComponent(component.Component):
    template_name = "progress/progress.html"

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

    class Media:
        css = "progress/progress.css"
        js = None

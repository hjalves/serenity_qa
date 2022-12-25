from django_components import component

from serenity_qa.apps.questions import progress


@component.register("progress")
class ProgressComponent(component.Component):
    template_name = "progress/progress.html"

    def get_context_data(self, id=None, arguments=None):
        if arguments and "id" in arguments:
            id = arguments["id"]
        return {
            "id": id or "",
            "videos_total": progress.videos_total(),
            "videos_worked": progress.videos_worked(),
            "videos_done": progress.videos_done(),
            "questions_added": progress.questions_added(),
            "questions_tagged": progress.questions_tagged(),
            "minutes_total": (total := progress.minutes_total()),
            "minutes_added": (added := progress.minutes_added()),
            "minutes_tagged": (tagged := progress.minutes_tagged()),
            "percentage_added": int(round(added / total * 100, 0)),
            "percentage_tagged": int(round(tagged / total * 100, 0)),
            "last_changed": progress.last_changed(),
        }

    class Media:
        css = "progress/progress.css"
        js = None

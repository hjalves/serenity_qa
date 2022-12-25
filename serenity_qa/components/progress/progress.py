from statistics import StatisticsError

from django_components import component

from serenity_qa.apps.questions import progress


@component.register("progress")
class ProgressComponent(component.Component):
    template_name = "progress/progress.html"

    def get_context_data(self, id=None, arguments=None):
        if arguments and "id" in arguments:
            id = arguments["id"]
        try:
            questions_total_expected, questions_interval = progress.estimate_questions()
        except StatisticsError:
            questions_total_expected, questions_interval = 0, 0
        return {
            "id": id or "",
            "videos_total": progress.videos_total(),
            "videos_worked": progress.videos_worked(),
            "videos_done": progress.videos_done(),
            "questions_added": (questions_added := progress.questions_added()),
            "questions_tagged": progress.questions_tagged(),
            "minutes_total": (minutes_total := progress.minutes_total()),
            "minutes_added": (minutes_added := progress.minutes_added()),
            "minutes_tagged": (minutes_tagged := progress.minutes_tagged()),
            "percentage_added": int(round(minutes_added / minutes_total * 100, 0)),
            "percentage_tagged": int(round(minutes_tagged / minutes_total * 100, 0)),
            "last_changed": progress.last_changed(),
            "questions_remaining": questions_total_expected - questions_added,
            "questions_interval": questions_interval,
        }

    class Media:
        css = "progress/progress.css"
        js = None

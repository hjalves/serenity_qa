from django_components import component


@component.register("progress")
class ProgressComponent(component.Component):
    template_name = "progress/progress.html"

    def get_context_data(self, id=None, arguments=None):
        if arguments and "id" in arguments:
            id = arguments["id"]
        return {"id": id or ""}

    class Media:
        css = "progress/progress.css"
        js = None

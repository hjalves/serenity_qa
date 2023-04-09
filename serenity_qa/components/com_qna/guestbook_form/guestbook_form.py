from django_components import component


@component.register("guestbook_form")
class GuestbookFormComponent(component.Component):
    template_name = "com_qna/guestbook_form/guestbook_form.html"

    class Media:
        css = "com_qna/guestbook_form/guestbook_form.css"
        js = (
            "js/htmx.min.js"
        )

    def get_context_data(self, form):
        return {
            'form': form
        }

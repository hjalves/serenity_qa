from django_components import component


@component.register("guestbook_message")
class GuestbookMessageComponent(component.Component):
    template_name = "com_qna/guestbook_message/guestbook_message.html"

    class Media:
        css = "com_qna/guestbook_message/guestbook_message.css"
        js = None

    def get_context_data(self, message):
        return {"message": message}

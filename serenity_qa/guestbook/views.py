from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView

from serenity_qa.guestbook.forms import GuestBookMessageForm
from serenity_qa.guestbook.models import Avatar, GuestBookMessage


class GuestBookView(FormView):
    template_name = "guestbook/guestbook.html"
    form_class = GuestBookMessageForm
    success_url = reverse_lazy("guestbook")

    def get_context_data(self, **kwargs):
        # self.request.session["test"] = "wtv"
        self.request.session.save()
        context = super().get_context_data(**kwargs)
        context["messages"] = GuestBookMessage.objects.order_by('-created_on')
        return context

    def get_initial(self):
        return {}

    def form_valid(self, form):
        instance = form.save()
        user_agent = getattr(self.request, "user_agent", None)
        ip_address = getattr(self.request, "ip_address", None)
        instance.user_agent = user_agent.ua_string[:500] if user_agent else ""
        instance.ip_address = ip_address
        instance.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        print("form invalid")
        print(form.errors)
        return super().form_invalid(form)


@csrf_exempt
def avatar_view(request):
    match request.method:
        case "GET" | "HEAD":
            avatar_slug = request.GET.get("avatar")
            avatar = get_object_or_404(Avatar, slug=avatar_slug)
            return HttpResponse(avatar.image_tag())
        case _:
            return HttpResponseNotAllowed(["GET"])

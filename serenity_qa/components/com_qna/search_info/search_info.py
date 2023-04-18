from django.utils.http import urlencode
from django_components import component


@component.register("search_info")
class SearchInfoComponent(component.Component):
    template_name = "com_qna/search_info/search_info.html"

    class Media:
        css = "com_qna/search_info/search_info.css"
        js = None

    def get_context_data(self, **kw):
        context = {}
        query = kw.get("query")
        context["query"] = query
        context["emoji"] = "🔍"
        context["results"] = kw.get("results") or 0
        context["query_urlencode"] = urlencode({"q": query})
        return context

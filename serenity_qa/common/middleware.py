from django.utils.functional import SimpleLazyObject
from ipware import get_client_ip

from serenity_qa.common.utils import get_user_agent


class UserAgentMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        return self.get_response(request)

    def process_request(self, request):
        request.user_agent = SimpleLazyObject(lambda: get_user_agent(request))
        request.ip_address = SimpleLazyObject(lambda: get_client_ip(request)[0])

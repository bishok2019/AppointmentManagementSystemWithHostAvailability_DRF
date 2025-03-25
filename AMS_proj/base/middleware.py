# base/middleware.py
import threading

request_local = threading.local()

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_local.user = getattr(request, 'user', None)
        response = self.get_response(request)
        return response

def get_current_user():
    return getattr(request_local, 'user', None)
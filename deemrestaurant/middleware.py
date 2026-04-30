import re
from django.conf import settings
from django.shortcuts import render

EXEMPT_URLS = [
    r'^admin/',
    r'^static/',
    r'^media/',
]


class MaintenanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(settings, 'MAINTENANCE_MODE', False):

            path = request.path_info.lstrip('/')

            # ✅ Allow admin, static, media
            if any(re.match(url, path) for url in EXEMPT_URLS):
                return self.get_response(request)

            # ✅ Allow YOU (local machine)
            if request.META.get('REMOTE_ADDR') in ['127.0.0.1', '::1']:
                return self.get_response(request)

            # ✅ Allow logged-in staff (optional)
            user = getattr(request, "user", None)
            if user and user.is_authenticated and user.is_staff:
                return self.get_response(request)

            # ❌ Everyone else sees maintenance
            return render(request, 'maintenance.html')

        return self.get_response(request)
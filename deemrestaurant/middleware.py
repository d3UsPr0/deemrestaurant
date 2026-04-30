import re
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse

EXEMPT_URLS = [
    r'^admin/',
    r'^static/',
    r'^media/',
]

class MaintenanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if maintenance mode is enabled
        if getattr(settings, 'MAINTENANCE_MODE', False):
            
            path = request.path_info.lstrip('/')
            
            # ✅ Allow admin, static, media URLs
            for url_pattern in EXEMPT_URLS:
                if re.match(url_pattern, path):
                    return self.get_response(request)
            
            # ✅ Allow localhost access
            remote_addr = request.META.get('REMOTE_ADDR', '')
            if remote_addr in ['127.0.0.1', '::1', 'localhost']:
                return self.get_response(request)
            
            # ✅ Allow logged-in staff/superusers
            user = getattr(request, "user", None)
            if user and user.is_authenticated:
                if user.is_staff or user.is_superuser:
                    return self.get_response(request)
            
            # ✅ Check for bypass session (optional)
            if request.session.get('bypass_maintenance', False):
                return self.get_response(request)
            
            # ❌ Everyone else sees maintenance page with 503 status
            try:
                return render(request, 'maintenance.html', status=503)
            except Exception as e:
                # Fallback if template is missing
                return HttpResponse(
                    '<h1>Under Maintenance</h1><p>Please check back soon.</p>',
                    status=503,
                    content_type='text/html'
                )
        
        return self.get_response(request)
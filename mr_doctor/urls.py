from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse


def healthz(request):
    checks = {"app": "ok", "database": "ok", "cache": "ok"}
    status = 200

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        checks["database"] = "error"
        status = 503

    try:
        cache.set("healthz", "ok", timeout=5)
        if cache.get("healthz") != "ok":
            raise RuntimeError("cache round trip failed")
    except Exception:
        checks["cache"] = "error"
        status = 503

    return JsonResponse(checks, status=status)



urlpatterns = [
    path('healthz/', healthz, name='healthz'),
    path('admin/', admin.site.urls),
    path('', include('products.urls')),
    path('cart/', include('cart.urls')),
    path('accounts/', include('accounts.urls')),
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(
        html_email_template_name='registration/password_reset_email.html'
    ), name='password_reset'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('chatbot/', include('Chatbot.urls')),
]

if getattr(settings, 'DJANGO_PROMETHEUS_AVAILABLE', False):
    urlpatterns.insert(0, path('', include('django_prometheus.urls')))

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

"""Root URL configuration."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse


def health_check(request):
    """Simple health check endpoint — returns 200 if server is running."""
    from django.db import connection
    db_status = "unknown"
    db_error = ""
    try:
        connection.ensure_connection()
        db_status = "connected"
    except Exception as e:
        db_status = "error"
        db_error = str(e)

    import os
    return JsonResponse({
        "status": "ok",
        "service": "GrantBridge API",
        "database": db_status,
        "db_error": db_error,
        "database_url_set": bool(os.environ.get("DATABASE_URL")),
        "settings": os.environ.get("DJANGO_SETTINGS_MODULE", "unknown"),
    })


urlpatterns = [
    path("", health_check),  # Root health check
    path("health/", health_check),
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.users.urls")),
    path("api/v1/pitches/", include("apps.pitches.urls")),
    path("api/v1/offers/", include("apps.offers.urls")),
    path("api/v1/payments/", include("apps.payments.urls")),
    path("api/v1/progress/", include("apps.progress.urls")),
    path("api/v1/verification/", include("apps.users.verification_urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

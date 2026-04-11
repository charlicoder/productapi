from django.http import JsonResponse
from django.utils import timezone
import os

def health_check(request):
    """
    Root health check endpoint.
    Returns basic API status and metadata.
    """
    return JsonResponse({
        "status": "up",
        "message": "Affiliate Products API is running smoothly",
        "version": "1.0.0",
        "timestamp": timezone.now().isoformat(),
        "environment": os.getenv("DJANGO_ENV", "development"),
        "documentation": {
            "swagger": "/api/docs/",
            "redoc": "/api/redoc/",
            "openapi": "/api/schema/"
        }
    }, status=200)

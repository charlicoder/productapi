from django.conf import settings
from django.urls import path
from django.views.decorators.cache import cache_page

from . import views

# Public GET endpoints: cached server-side and sent with Cache-Control: max-age (0 disables).
cached = cache_page(settings.API_CACHE_SECONDS) if settings.API_CACHE_SECONDS > 0 else (lambda v: v)

urlpatterns = [
    path("products/", cached(views.ProductList.as_view())),
    path("hero/", cached(views.Hero.as_view())),
    path("categories/", cached(views.Categories.as_view())),
    path("products/<slug:slug>/", cached(views.ProductDetail.as_view())),
]

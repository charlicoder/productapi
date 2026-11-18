from django.core.cache import cache
from django.db.models.signals import post_delete, post_save

from .models import Product, Variant, VariantImage


def _clear(**_):
    cache.clear()  # any catalog edit (admin or import) drops cached API responses


def connect():
    for model in (Product, Variant, VariantImage):
        post_save.connect(_clear, sender=model, dispatch_uid=f"clear-{model.__name__}-save")
        post_delete.connect(_clear, sender=model, dispatch_uid=f"clear-{model.__name__}-delete")

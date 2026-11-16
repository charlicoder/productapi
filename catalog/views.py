from django.db.models import Prefetch, Q
from rest_framework import generics

from .models import Product, Variant
from .serializers import ProductDetailSerializer, ProductListSerializer


def _active():
    return Product.objects.filter(is_active=True).prefetch_related(
        Prefetch("variants", queryset=Variant.objects.prefetch_related("images"))
    )


class ProductList(generics.ListAPIView):
    serializer_class = ProductListSerializer

    def get_queryset(self):
        qs = _active()
        q = self.request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(title_en__icontains=q) | Q(title_ar__icontains=q) | Q(brand__icontains=q) | Q(asin__icontains=q))
        cat = self.request.query_params.get("category", "").strip()
        if cat:
            qs = qs.filter(category=cat)
        return qs


class ProductDetail(generics.RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return _active()

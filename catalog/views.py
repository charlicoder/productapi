from django.db.models import Prefetch, Q
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CATEGORY_CHOICES, Product, Variant
from .serializers import ProductDetailSerializer, ProductListSerializer
from .taxonomy import TAXONOMY, sub_query

HERO_SIZE = 5


def _active():
    return Product.objects.filter(is_active=True).prefetch_related(
        Prefetch("variants", queryset=Variant.objects.prefetch_related("images"))
    )


class ProductList(generics.ListAPIView):
    serializer_class = ProductListSerializer

    def get_queryset(self):
        qs = _active()
        p = self.request.query_params
        q = p.get("q", "").strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(title_en__icontains=q) | Q(title_ar__icontains=q) | Q(brand__icontains=q) | Q(asin__icontains=q))
        cat = p.get("category", "").strip()
        if cat:
            qs = qs.filter(category=cat)
            sub = sub_query(cat, p.get("sub", "").strip())
            if sub is not None:
                qs = qs.filter(sub)
        return qs


class Hero(APIView):
    """Up to 5 slides for a category page: admin-featured products first, topped up with the newest."""

    def get(self, request):
        cat = request.query_params.get("category", "").strip()
        base = _active().filter(variants__images__isnull=False).distinct()
        if cat:
            base = base.filter(category=cat)
        picked = list(base.filter(is_featured=True)[:HERO_SIZE])
        if len(picked) < HERO_SIZE:
            ids = [p.id for p in picked]
            picked += list(base.exclude(id__in=ids)[: HERO_SIZE - len(picked)])
        return Response(ProductListSerializer(picked, many=True, context={"request": request}).data)


class Categories(APIView):
    """Product counts per category and sub-category, so the storefront can hide empty tabs."""

    def get(self, request):
        rows = list(Product.objects.filter(is_active=True).values("category", "category_path"))
        out = {}
        for slug, _label in CATEGORY_CHOICES:
            subs = {}
            for sub in TAXONOMY.get(slug, {}):
                subs[sub] = Product.objects.filter(is_active=True, category=slug).filter(sub_query(slug, sub)).count()
            out[slug] = {"count": sum(1 for r in rows if r["category"] == slug), "subs": subs}
        return Response(out)


class ProductDetail(generics.RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return _active()

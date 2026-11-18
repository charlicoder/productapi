from django.db.models import Prefetch, Q, prefetch_related_objects
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .models import CATEGORY_CHOICES, Product, Variant
from .serializers import ProductDetailSerializer, ProductListSerializer
from .taxonomy import TAXONOMY, row_matches, sub_query

HERO_SIZE = 5
_VARIANTS = Prefetch("variants", queryset=Variant.objects.prefetch_related("images"))


def _active():
    return Product.objects.filter(is_active=True)


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

    def paginate_queryset(self, queryset):
        page = super().paginate_queryset(queryset)
        # Cards read the precomputed `card_images`; only products without it need the variant tree.
        if page:
            prefetch_related_objects([p for p in page if not p.card_images], _VARIANTS)
        return page


class Hero(APIView):
    """Up to 5 slides for a category page: admin-featured products first, topped up with the newest."""

    def get(self, request):
        cat = request.query_params.get("category", "").strip()
        base = _active()
        if cat:
            base = base.filter(category=cat)
        pool = list(base.filter(is_featured=True)[: HERO_SIZE * 2]) + list(base.filter(is_featured=False)[: HERO_SIZE * 2])
        prefetch_related_objects([p for p in pool if not p.card_images], _VARIANTS)
        data = ProductListSerializer(pool, many=True, context={"request": request}).data
        return Response([d for d in data if d["images"]][:HERO_SIZE])


class Categories(APIView):
    """Product counts per category and sub-category (one query), so the storefront can hide empty tabs."""

    def get(self, request):
        rows = list(_active().values("category", "category_path", "title", "title_en", "brand"))
        out = {}
        for slug, _label in CATEGORY_CHOICES:
            mine = [r for r in rows if r["category"] == slug]
            out[slug] = {"count": len(mine), "subs": {s: sum(1 for r in mine if row_matches(slug, s, r)) for s in TAXONOMY.get(slug, {})}}
        return Response(out)


class ProductDetail(generics.RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return _active().prefetch_related(_VARIANTS)


class Subscribe(APIView):
    """POST {country_code, phone, country?, language?} -> 202. Stored asynchronously."""

    throttle_classes = [AnonRateThrottle]
    authentication_classes = []

    def post(self, request):
        from . import subscribe

        d = request.data
        try:
            phone, dial = subscribe.normalize(str(d.get("country_code", "")), str(d.get("phone", "")))
        except ValueError as e:
            return Response({"error": str(e)}, status=400)
        subscribe.submit(
            phone, dial,
            country=str(d.get("country", ""))[:2].upper(),
            language=str(d.get("language", ""))[:5],
            source=str(d.get("source", ""))[:40],
        )
        return Response({"status": "accepted"}, status=202)

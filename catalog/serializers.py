from rest_framework import serializers

from .models import Product, Variant, VariantImage

CARD_IMAGE_LIMIT = 8


class VariantImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantImage
        fields = ("slot", "url", "thumbnail", "full_size")


class VariantSerializer(serializers.ModelSerializer):
    label = serializers.CharField(read_only=True)
    images = VariantImageSerializer(many=True, read_only=True)

    class Meta:
        model = Variant
        fields = ("id", "asin", "label", "color", "style", "price", "swatch_image", "unavailable", "videos", "images")


class LocalizedMixin:
    def _lang(self):
        req = self.context.get("request")
        return (req.query_params.get("lang", "en") if req else "en").lower()[:2]

    def get_title(self, obj):
        return obj.localized("title", self._lang())

    def get_subtitle(self, obj):
        return obj.localized("subtitle", self._lang())

    # Explicit per-language fields so clients (and caches) don't depend on ?lang=.
    # English falls back to the original scraped text; Arabic stays empty if not translated.
    def get_title_en(self, obj):
        return obj.title_en or obj.title

    def get_title_ar(self, obj):
        return obj.title_ar

    def get_subtitle_en(self, obj):
        return obj.subtitle_en or obj.subtitle

    def get_subtitle_ar(self, obj):
        return obj.subtitle_ar


class ProductListSerializer(LocalizedMixin, serializers.ModelSerializer):
    """Card payload: title + a handful of images only."""

    title = serializers.SerializerMethodField()
    title_en = serializers.SerializerMethodField()
    title_ar = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ("slug", "title", "title_en", "title_ar", "images")

    def get_images(self, obj):
        # Needs prefetch of variants__images. First image of each variant first (variety), then the rest.
        variants = list(obj.variants.all())
        firsts, rest = [], []
        for v in variants:
            imgs = list(v.images.all())
            if imgs:
                firsts.append(imgs[0].url)
                rest.extend(i.url for i in imgs[1:])
        out = []
        for u in firsts + rest:
            if u not in out:
                out.append(u)
            if len(out) >= CARD_IMAGE_LIMIT:
                break
        return out


class ProductDetailSerializer(LocalizedMixin, serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    subtitle = serializers.SerializerMethodField()
    title_en = serializers.SerializerMethodField()
    title_ar = serializers.SerializerMethodField()
    subtitle_en = serializers.SerializerMethodField()
    subtitle_ar = serializers.SerializerMethodField()
    variants = VariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "slug", "asin", "title", "subtitle", "title_en", "title_ar", "subtitle_en", "subtitle_ar", "brand", "affiliate_link", "affiliate_site",
            "category_path", "categories", "tags", "sizes", "videos", "variants",
        )

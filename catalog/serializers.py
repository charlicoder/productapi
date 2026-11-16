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


class ProductListSerializer(serializers.ModelSerializer):
    """Card payload: title + a handful of images only."""

    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ("slug", "title", "images")

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


class ProductDetailSerializer(serializers.ModelSerializer):
    variants = VariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "slug", "asin", "title", "subtitle", "brand", "affiliate_link", "affiliate_site",
            "category_path", "categories", "tags", "sizes", "videos", "variants",
        )

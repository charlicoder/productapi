from django.db import models


CATEGORY_CHOICES = [
    ("apparel", "Apparel"),
    ("footwear-bags", "Footwear & Bags"),
    ("beauty-health", "Beauty, Skincare & Health Care"),
    ("home-living", "Home & Living"),
]


class Product(models.Model):
    """One affiliate product (one Amazon parent/ASIN page)."""

    asin = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    # Original scraped text (kept as the fallback) + AI-polished, localized copy.
    title = models.CharField(max_length=500)
    subtitle = models.TextField(blank=True)
    title_en = models.CharField("title (English)", max_length=200, blank=True)
    subtitle_en = models.TextField("subtitle (English)", blank=True)
    title_ar = models.CharField("title (Arabic)", max_length=300, blank=True)
    subtitle_ar = models.TextField("subtitle (Arabic)", blank=True)
    brand = models.CharField(max_length=200, blank=True, db_index=True)
    url = models.URLField(max_length=1000, blank=True, help_text="Original product page")
    affiliate_link = models.URLField(max_length=1000)
    affiliate_site = models.CharField(max_length=100, blank=True, default="Amazon")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, blank=True, db_index=True, help_text="Storefront filter group")
    category_path = models.CharField(max_length=500, blank=True, db_index=True)

    # Small list-like attributes: JSON keeps the schema simple (no join tables to maintain).
    categories = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)
    sizes = models.JSONField(default=list, blank=True)
    countries = models.JSONField(default=list, blank=True)
    videos = models.JSONField(default=list, blank=True)

    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True, help_text="Show in the hero slider of its category page")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def localized(self, field, lang):
        """title/subtitle in `lang`, falling back ar -> en -> original."""
        chain = {"ar": ("ar", "en"), "en": ("en",)}.get(lang, ("en",))
        for code in chain:
            v = getattr(self, f"{field}_{code}")
            if v:
                return v
        return getattr(self, field)

    def __str__(self):
        return self.title_en or self.title


class Variant(models.Model):
    """A color / style option of a product, each with its own image set."""

    product = models.ForeignKey(Product, related_name="variants", on_delete=models.CASCADE)
    asin = models.CharField(max_length=20, blank=True)
    color = models.CharField(max_length=200, blank=True)
    style = models.CharField(max_length=200, blank=True, help_text="Other variation, e.g. pattern")
    price = models.CharField(max_length=40, blank=True, help_text='Display price, e.g. "$49.99"')
    swatch_image = models.URLField(max_length=1000, blank=True)
    unavailable = models.BooleanField(default=False)
    videos = models.JSONField(default=list, blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    @property
    def label(self):
        return " / ".join(x for x in (self.color, self.style) if x) or self.asin

    def __str__(self):
        return f"{self.product_id}: {self.label}"


class VariantImage(models.Model):
    variant = models.ForeignKey(Variant, related_name="images", on_delete=models.CASCADE)
    position = models.PositiveSmallIntegerField(default=0)
    slot = models.CharField(max_length=20, blank=True)
    url = models.URLField(max_length=1000, help_text="Large image")
    thumbnail = models.URLField(max_length=1000, blank=True)
    full_size = models.URLField(max_length=1000, blank=True)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"{self.variant_id}#{self.position}"

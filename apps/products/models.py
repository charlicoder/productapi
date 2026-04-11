"""
Django models for Affiliate Products with multi-language support.

Uses django-parler for translations with optimized database indexing.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from parler.models import TranslatableModel, TranslatedFields


class TimeStampedModel(models.Model):
    """Abstract base model with timestamp fields."""

    created_at = models.DateTimeField(_("created at"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        abstract = True


class Brand(TimeStampedModel):
    """Brand model - Multi-language removed as requested."""

    name = models.CharField(_("brand name"), max_length=255)
    description = models.TextField(_("description"), blank=True, default="")
    slug = models.SlugField(_("slug"), max_length=255, unique=True, db_index=True)
    url = models.URLField(_("brand URL"), max_length=500, blank=True, default="")
    logo = models.URLField(_("logo URL"), max_length=500, blank=True, default="")
    is_active = models.BooleanField(_("is active"), default=True, db_index=True)

    class Meta:
        verbose_name = _("brand")
        verbose_name_plural = _("brands")
        indexes = [models.Index(fields=["slug", "is_active"])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Category(TranslatableModel, TimeStampedModel):
    """
    Category model with multi-language support.

    Translatable fields: name, description
    """

    translations = TranslatedFields(
        name=models.CharField(_("category name"), max_length=255),
        description=models.TextField(_("description"), blank=True, default=""),
    )

    slug = models.SlugField(_("slug"), max_length=255, unique=True, db_index=True)
    icon = models.CharField(_("icon"), max_length=100, blank=True, default="")
    is_active = models.BooleanField(_("is active"), default=True, db_index=True)
    order = models.PositiveIntegerField(_("display order"), default=0)

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")
        ordering = ["order", "translations__name"]
        indexes = [
            models.Index(fields=["slug", "is_active"]),
            models.Index(fields=["order"]),
        ]

    def __str__(self):
        return (
            self.safe_translation_getter("name", any_language=True)
            or f"Category {self.pk}"
        )

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            name = self.safe_translation_getter("name", any_language=True)
            if name:
                self.slug = slugify(name)
        super().save(*args, **kwargs)


class SubCategory(TranslatableModel, TimeStampedModel):
    """
    SubCategory model with multi-language support.

    Translatable fields: name, description
    """

    translations = TranslatedFields(
        name=models.CharField(_("subcategory name"), max_length=255),
        description=models.TextField(_("description"), blank=True, default=""),
    )

    slug = models.SlugField(_("slug"), max_length=255, db_index=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="subcategories",
        verbose_name=_("parent category"),
    )
    icon = models.CharField(_("icon"), max_length=100, blank=True, default="")
    is_active = models.BooleanField(_("is active"), default=True, db_index=True)
    order = models.PositiveIntegerField(_("display order"), default=0)

    class Meta:
        verbose_name = _("subcategory")
        verbose_name_plural = _("subcategories")
        ordering = ["order", "translations__name"]
        unique_together = [["slug", "category"]]
        indexes = [
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["slug", "category"]),
        ]

    def __str__(self):
        return (
            self.safe_translation_getter("name", any_language=True)
            or f"SubCategory {self.pk}"
        )

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            name = self.safe_translation_getter("name", any_language=True)
            if name:
                self.slug = slugify(name)
        super().save(*args, **kwargs)


class Product(TranslatableModel, TimeStampedModel):
    """
    Main Product model with multi-language support.

    Translatable fields: title, description, shipping, returns

    JSON fields: images, videos, features, price_info, meta
    Comma-separated: tags
    Foreign keys: brand, category, sub_category
    Choices: product_type, platform
    """

    class Platform(models.TextChoices):
        AMAZON = "amazon", _("Amazon")
        EBAY = "ebay", _("eBay")
        ALIEXPRESS = "aliexpress", _("AliExpress")
        WALMART = "walmart", _("Walmart")
        TARGET = "target", _("Target")
        ETSY = "etsy", _("Etsy")
        OTHER = "other", _("Other")

    class ProductType(models.TextChoices):
        ELECTRONICS = "electronics", _("Electronics")
        CLOTHING = "clothing", _("Clothing")
        HOME_GARDEN = "home_garden", _("Home & Garden")
        SPORTS = "sports", _("Sports & Outdoors")
        BEAUTY = "beauty", _("Beauty & Personal Care")
        TOYS = "toys", _("Toys & Games")
        BOOKS = "books", _("Books")
        AUTOMOTIVE = "automotive", _("Automotive")
        GROCERY = "grocery", _("Grocery")
        HEALTH = "health", _("Health & Household")
        PET = "pet", _("Pet Supplies")
        OFFICE = "office", _("Office Products")
        OTHER = "other", _("Other")

    # Translatable fields
    translations = TranslatedFields(
        title=models.CharField(_("product title"), max_length=500),
        description=models.TextField(_("description"), blank=True, default=""),
        shipping=models.CharField(
            _("shipping info"), max_length=500, blank=True, null=True
        ),
        returns=models.CharField(
            _("returns info"), max_length=500, blank=True, null=True
        ),
    )

    # Core identification
    product_asin = models.CharField(
        _("product ASIN/ID"), max_length=50, unique=True, db_index=True
    )

    # Slug field - auto-generated from title
    slug = models.SlugField(
        _("slug"),
        max_length=550,
        unique=True,
        db_index=True,
        blank=True,
        help_text=_("URL-friendly version of the title. Auto-generated if left blank."),
    )

    platform = models.CharField(
        _("platform"),
        max_length=20,
        choices=Platform.choices,
        default=Platform.AMAZON,
        db_index=True,
    )
    af_link = models.URLField(_("affiliate link"), max_length=2000)

    # Relationships (ForeignKey)
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        related_name="products",
        verbose_name=_("brand"),
        null=True,
        blank=True,
        db_index=True,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name="products",
        verbose_name=_("category"),
        null=True,
        blank=True,
        db_index=True,
    )
    sub_category = models.ForeignKey(
        SubCategory,
        on_delete=models.SET_NULL,
        related_name="products",
        verbose_name=_("subcategory"),
        null=True,
        blank=True,
        db_index=True,
    )

    # Choice field
    product_type = models.CharField(
        _("product type"),
        max_length=20,
        choices=ProductType.choices,
        default=ProductType.OTHER,
        db_index=True,
    )

    # JSON fields for structured data
    price_info = models.JSONField(
        _("price information"),
        default=dict,
        blank=True,
        help_text=_(
            "Stores price, regular_price, cost_savings, discount_percent, savings_percent"
        ),
    )
    features = models.JSONField(
        _("product features"),
        default=list,
        blank=True,
        help_text=_("List of feature objects with key and value"),
    )
    images = models.JSONField(
        _("product images"),
        default=list,
        blank=True,
        help_text=_("List of image objects with image, alt_text, is_featured, order"),
    )
    videos = models.JSONField(
        _("product videos"),
        default=list,
        blank=True,
        help_text=_("List of video objects with video, title, is_featured, order"),
    )
    meta = models.JSONField(
        _("SEO meta data"),
        default=dict,
        blank=True,
        help_text=_("SEO metadata: page_header, meta_description, meta_keywords, etc."),
    )

    # Comma-separated tags stored as text
    tags = models.TextField(
        _("tags"), blank=True, default="", help_text=_("Comma-separated list of tags")
    )

    # Additional fields
    rating = models.DecimalField(
        _("rating"),
        max_digits=2,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        db_index=True,
    )

    # Status fields
    is_active = models.BooleanField(_("is active"), default=True, db_index=True)
    is_featured = models.BooleanField(_("is featured"), default=False, db_index=True)
    view_count = models.PositiveIntegerField(_("view count"), default=0)
    click_count = models.PositiveIntegerField(_("click count"), default=0)

    class Meta:
        verbose_name = _("product")
        verbose_name_plural = _("products")
        ordering = ["-created_at"]
        indexes = [
            # Composite indexes for common query patterns
            models.Index(fields=["slug"]),
            models.Index(fields=["platform", "is_active"]),
            models.Index(fields=["product_type", "is_active"]),
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["brand", "is_active"]),
            models.Index(fields=["is_active", "is_featured"]),
            models.Index(fields=["rating", "is_active"]),
            models.Index(fields=["-created_at", "is_active"]),
        ]

    def __str__(self):
        if self.pk:
            title = self.safe_translation_getter("title", any_language=True)
            if title:
                return title
        return self.product_asin or f"Product {self.pk}"

    def save(self, *args, **kwargs):
        """
        Auto-generate slug from title if not provided.

        Note: For new objects, slug is generated after initial save
        because translations require a primary key.
        """
        is_new = self.pk is None

        # For existing objects without slug, try to generate one
        if not is_new and not self.slug:
            self._generate_slug_from_title()

        # For new objects without slug, use ASIN as temporary slug
        if is_new and not self.slug:
            # Use ASIN as initial slug, will be updated after translations are added
            self.slug = slugify(self.product_asin) or self.product_asin.lower()

        super().save(*args, **kwargs)

    def _generate_slug_from_title(self):
        """Internal method to generate slug from title."""
        try:
            title = self.safe_translation_getter("title", any_language=True)
            if title:
                base_slug = slugify(title)
                if base_slug:
                    slug = base_slug
                    # Ensure uniqueness by appending ASIN if needed
                    if Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                        slug = f"{base_slug}-{self.product_asin.lower()}"
                    self.slug = slug[:550]  # Ensure it fits in the field
                    return True
        except Exception:
            pass
        return False

    def generate_slug(self):
        """
        Manually regenerate slug from current title.
        Call this after translations have been added.

        Returns the new slug or None if generation failed.
        """
        if not self.pk:
            return None

        try:
            title = self.safe_translation_getter("title", any_language=True)
            if title:
                base_slug = slugify(title)
                if base_slug:
                    slug = base_slug
                    if Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                        slug = f"{base_slug}-{self.product_asin.lower()}"
                    self.slug = slug[:550]
                    return self.slug
        except Exception:
            pass
        return None

    def update_slug_from_title(self):
        """
        Update slug from title and save.
        Convenience method that generates slug and saves the model.
        """
        if self.generate_slug():
            self.save(update_fields=["slug"])
            return True
        return False

    @property
    def tags_list(self):
        """Return tags as a list."""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]

    @tags_list.setter
    def tags_list(self, value):
        """Set tags from a list."""
        if isinstance(value, list):
            self.tags = ", ".join(value)
        else:
            self.tags = value

    @property
    def current_price(self):
        """Get current price from price_info."""
        return self.price_info.get("price") if self.price_info else None

    @property
    def featured_image(self):
        """Get the featured image URL."""
        if not self.images:
            return None
        for img in self.images:
            if img.get("is_featured"):
                return img.get("image")
        return self.images[0].get("image") if self.images else None

    def increment_view(self):
        """Increment view count atomically."""
        Product.objects.filter(pk=self.pk).update(view_count=models.F("view_count") + 1)

    def increment_click(self):
        """Increment click count atomically."""
        Product.objects.filter(pk=self.pk).update(
            click_count=models.F("click_count") + 1
        )

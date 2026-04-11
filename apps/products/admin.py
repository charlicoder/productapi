from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from parler.admin import TranslatableAdmin
from .models import Brand, Category, SubCategory, Product


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    """Standard ModelAdmin (Brand is no longer translatable)."""

    list_display = ["name", "preview_logo", "slug", "is_active", "created_at"]
    search_fields = ["name", "slug"]
    list_filter = ["is_active"]

    def preview_logo(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="height: 30px; width: auto;" />', obj.logo
            )
        return "-"

    preview_logo.short_description = "Logo"


@admin.register(Category)
class CategoryAdmin(TranslatableAdmin):
    list_display = ["get_name", "slug", "order", "is_active"]
    search_fields = ["translations__name", "slug"]

    def get_name(self, obj):
        return obj.safe_translation_getter("name", any_language=True)

    get_name.short_description = "Name"


@admin.register(SubCategory)
class SubCategoryAdmin(TranslatableAdmin):
    list_display = ["get_name", "category", "slug", "is_active"]
    list_filter = ["category", "is_active"]
    raw_id_fields = ["category"]

    def get_name(self, obj):
        return obj.safe_translation_getter("name", any_language=True)

    get_name.short_description = "Name"


@admin.register(Product)
class ProductAdmin(TranslatableAdmin):
    # 'preview_media' used for list view
    list_display = [
        "get_title",
        "product_asin",
        "preview_media",
        "brand",
        "category",
        "is_active",
        "is_featured",
    ]
    list_filter = ["platform", "brand", "category", "is_active", "is_featured"]

    # Updated: use brand__name (Brand is not translatable)
    search_fields = ["translations__title", "product_asin", "slug", "brand__name"]

    # 'preview_media_large' is a method, must be in readonly_fields to show in fieldsets
    readonly_fields = ["preview_media_large", "created_at", "updated_at"]
    raw_id_fields = ["brand", "category", "sub_category"]

    def get_fieldsets(self, request, obj=None):
        """
        In TranslatableAdmin, we exclude translatable fields from fieldsets.
        Parler will automatically render them in tabs.
        """
        return [
            (
                "Core Info",
                {
                    "fields": (
                        "product_asin",
                        "slug",
                        "platform",
                        "af_link",
                        "product_type",
                    ),
                    "description": "Basic product identification and affiliate links.",
                },
            ),
            ("Hierarchy", {"fields": ("brand", "category", "sub_category")}),
            (
                "Media Preview",
                {
                    "fields": ("preview_media_large",),
                },
            ),
            (
                "Data & Media",
                {
                    "fields": (
                        "price_info",
                        "features",
                        "images",
                        "videos",
                        "tags",
                        "meta",
                    ),
                    "classes": ("collapse",),
                },
            ),
            (
                "Status & Stats",
                {
                    "fields": (
                        "rating",
                        "is_active",
                        "is_featured",
                        "view_count",
                        "click_count",
                    ),
                },
            ),
            (
                "Timestamps",
                {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
            ),
        ]

    def get_title(self, obj):
        return (
            obj.safe_translation_getter("title", any_language=True) or obj.product_asin
        )

    get_title.short_description = "Title"

    def preview_media(self, obj):
        """Thumbnail for list view."""
        if obj.images and len(obj.images) > 0:
            img_url = obj.images[0].get("image")
            return format_html(
                '<img src="{}" style="height: 35px; width: auto; border-radius: 4px;" />',
                img_url,
            )
        return "-"

    preview_media.short_description = "Img"

    def preview_media_large(self, obj):
        """Gallery and Video preview for edit form."""
        # Handle new objects without data
        if not obj or not (obj.images or obj.videos):
            return "No media files to preview."

        html_output = [
            '<div style="display: flex; flex-wrap: wrap; gap: 15px; background: #f8f8f8; padding: 15px; border-radius: 8px; border: 1px solid #ddd;">'
        ]

        # Images
        if obj.images:
            for img in obj.images:
                url = img.get("image")
                if url:
                    html_output.append(
                        format_html(
                            '<div style="text-align:center;"><img src="{}" style="height: 120px; border: 2px solid #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" /><br/><small>Image</small></div>',
                            url,
                        )
                    )

        # Videos
        if obj.videos:
            for vid in obj.videos:
                url = vid.get("video", "")
                if "youtube.com" in url or "youtu.be" in url:
                    vid_id = url.split("=")[-1] if "=" in url else url.split("/")[-1]
                    html_output.append(
                        format_html(
                            '<div><iframe width="200" height="120" src="https://www.youtube.com/embed/{}" frameborder="0" allowfullscreen></iframe><br/><small>YouTube</small></div>',
                            vid_id,
                        )
                    )
                elif url:
                    html_output.append(
                        format_html(
                            '<div><video width="200" height="120" controls><source src="{}">Video</video><br/><small>Video</small></div>',
                            url,
                        )
                    )

        html_output.append("</div>")
        return mark_safe("".join(html_output))

    preview_media_large.short_description = "Media Content Preview"

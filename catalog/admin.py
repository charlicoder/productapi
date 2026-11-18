import json

from django import forms
from django.contrib import admin, messages
from django.utils.html import format_html, format_html_join
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import path, reverse

from .importer import import_products
from .models import Product, Variant, VariantImage


class ImportForm(forms.Form):
    file = forms.FileField(required=False, label="JSON file")
    pasted = forms.CharField(
        required=False, label="…or paste JSON", widget=forms.Textarea(attrs={"rows": 10, "cols": 80})
    )

    def clean(self):
        data = super().clean()
        raw = data["file"].read() if data.get("file") else (data.get("pasted") or "").strip()
        if not raw:
            raise forms.ValidationError("Upload a file or paste JSON.")
        try:
            data["payload"] = json.loads(raw)
        except ValueError as e:
            raise forms.ValidationError(f"Invalid JSON: {e}")
        return data


def _video_html(urls):
    urls = [u for u in (urls or []) if u]
    if not urls:
        return "No video"
    return format_html_join(
        "",
        '<div style="margin:0 12px 12px 0;display:inline-block"><video src="{}" controls preload="metadata" '
        'style="max-width:320px;max-height:320px;border-radius:8px"></video><br><a href="{}" target="_blank" rel="noopener">Open video link</a></div>',
        ((u, u) for u in urls),
    )


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 0
    fields = ("color", "style", "price", "asin", "swatch_image", "unavailable", "position")
    show_change_link = True


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("display_title", "images_gallery", "videos_links", "category", "is_featured", "brand", "asin", "is_active", "updated_at")
    list_filter = ("category", "is_featured", "is_active", "affiliate_site", "brand")
    search_fields = ("title", "title_en", "title_ar", "asin", "brand", "category_path")
    list_editable = ("is_active", "is_featured")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [VariantInline]
    readonly_fields = ("video_preview",)
    change_list_template = "admin/catalog/product/change_list.html"

    @admin.display(description="Video preview")
    def video_preview(self, obj):
        return _video_html(obj.videos)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("variants__images")

    @admin.display(description="Title", ordering="title_en")
    def display_title(self, obj):
        return obj.title_en or obj.title

    @staticmethod
    def _all_videos(obj):
        seen = []
        for u in list(obj.videos or []) + [u for v in obj.variants.all() for u in (v.videos or [])]:
            if u and u not in seen:
                seen.append(u)
        return seen

    @admin.display(description="Images")
    def images_gallery(self, obj):
        n = sum(len(v.images.all()) for v in obj.variants.all())
        if not n:
            return "—"
        url = reverse("admin:catalog_product_images", args=[obj.pk])
        return format_html('<a href="{}">🖼 View {} image{}</a>', url, n, "" if n == 1 else "s")

    @admin.display(description="Videos")
    def videos_links(self, obj):
        n = len(self._all_videos(obj))
        if not n:
            return "—"
        url = reverse("admin:catalog_product_videos", args=[obj.pk])
        return format_html('<a href="{}">▶ View {} video{}</a>', url, n, "" if n == 1 else "s")

    def _media_page(self, request, pk, template, title, extra):
        product = self.get_object(request, pk)
        if product is None:
            raise Http404
        ctx = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "product": product,
            "title": f"{title}: {product.title}",
            **extra(product),
        }
        return render(request, template, ctx)

    def images_view(self, request, pk):
        def extra(p):
            return {"groups": [(v, list(v.images.all())) for v in p.variants.all()]}
        return self._media_page(request, pk, "admin/catalog/product/images.html", "Images", extra)

    def videos_view(self, request, pk):
        def extra(p):
            groups = []
            if p.videos:
                groups.append(("Product videos", list(p.videos)))
            for v in p.variants.all():
                vids = [u for u in (v.videos or []) if u not in (p.videos or [])]
                if vids:
                    groups.append((f"Variant: {v.label}", vids))
            return {"groups": groups}
        return self._media_page(request, pk, "admin/catalog/product/videos.html", "Videos", extra)

    def get_urls(self):
        wrap = self.admin_site.admin_view
        return [
            path("import-json/", wrap(self.import_view), name="catalog_product_import"),
            path("<int:pk>/images/", wrap(self.images_view), name="catalog_product_images"),
            path("<int:pk>/videos/", wrap(self.videos_view), name="catalog_product_videos"),
        ] + super().get_urls()

    def import_view(self, request):
        form = ImportForm(request.POST or None, request.FILES or None)
        if request.method == "POST" and form.is_valid():
            r = import_products(form.cleaned_data["payload"])
            messages.success(request, f"Imported: {r.created} created, {r.updated} updated, {r.skipped} skipped.")
            for e in r.errors[:20]:
                messages.warning(request, e)
            return redirect(reverse("admin:catalog_product_changelist"))
        ctx = {**self.admin_site.each_context(request), "form": form, "opts": self.model._meta, "title": "Import products from JSON"}
        return render(request, "admin/catalog/product/import.html", ctx)


class ImageInline(admin.TabularInline):
    model = VariantImage
    extra = 0


@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.product.refresh_card_images()  # images were edited: keep list cards in sync

    list_display = ("product", "color", "style", "price", "unavailable")
    search_fields = ("product__title", "color", "asin")
    autocomplete_fields = ("product",)
    readonly_fields = ("video_preview",)

    @admin.display(description="Video preview")
    def video_preview(self, obj):
        return _video_html(obj.videos)
    inlines = [ImageInline]

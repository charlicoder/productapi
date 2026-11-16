"""Import product JSON (list of products, or a single product object) with upsert-by-ASIN."""
import json
from dataclasses import dataclass, field

from django.db import transaction
from django.utils.text import slugify

from .models import CATEGORY_CHOICES, Product, Variant, VariantImage


@dataclass
class ImportResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list = field(default_factory=list)


def _list(v):
    return [x for x in v] if isinstance(v, (list, tuple)) else []


def _make_slug(title, asin):
    return f"{slugify(title)[:80]}-{asin.lower()}".strip("-")


_RULES = [
    ("footwear-bags", ("shoe", "sneaker", "boot", "sandal", "handbag", "bag", "backpack", "luggage", "wallet", "purse")),
    ("tech-audio", ("electronic", "headphone", "earbud", "audio", "speaker", "computer", "camera", "phone", "laptop", "tablet", "wearable")),
    ("home-living", ("home", "kitchen", "furniture", "bedding", "decor", "garden", "appliance", "lighting")),
    ("apparel", ("clothing", "apparel", "jacket", "dress", "sweat", "shirt", "pants", "coat")),
]


def detect_category(category_path, title=""):  # title kept for API compat; brands like "GARDEN" cause false hits
    parts = [p.strip() for p in (category_path or "").split(">") if p.strip()]
    clothing_root = bool(parts) and parts[0].lower().startswith("clothing, shoes")
    text = " ".join(parts[1:] if clothing_root else parts).lower() 
    for cat, words in _RULES:
        if any(w in text for w in words):
            return cat
    return "apparel" if clothing_root else ""


def _import_one(data):
    asin = (data.get("asin") or "").strip()
    link = data.get("affiliate_link") or ""
    if not asin or not link:
        raise ValueError("'asin' and 'affiliate_link' are required")
    title = data.get("title") or data.get("full_title") or asin

    defaults = dict(
        title=title[:500],
        subtitle=data.get("subtitle") or "",
        brand=(data.get("brand") or "")[:200],
        url=data.get("url") or "",
        affiliate_link=link,
        affiliate_site=data.get("affiliate_site") or "Amazon",
        category_path=data.get("category_path") or " > ".join(_list(data.get("categories"))),
        categories=_list(data.get("categories")),
        tags=_list(data.get("tags")),
        sizes=_list(data.get("sizes")),
        countries=_list(data.get("countries")),
        videos=_list(data.get("videos")),
    )
    existing = Product.objects.filter(asin=asin).first()
    # Localized copy (from scripts/enrich_products.py). Only overwrite what the file provides.
    for k in ("title_en", "subtitle_en", "title_ar", "subtitle_ar"):
        if data.get(k):
            defaults[k] = data[k]
    explicit = (data.get("category") or "").strip()
    valid = {c for c, _ in CATEGORY_CHOICES}
    if explicit in valid:
        defaults["category"] = explicit
    elif not existing or not existing.category:  # never clobber a category edited in admin
        defaults["category"] = detect_category(defaults["category_path"], title)
    # Keep an existing slug stable (URLs/SEO); new products slug from the polished English title.
    if not existing:
        defaults["slug"] = _make_slug(defaults.get("title_en") or title, asin)
    product, created = Product.objects.update_or_create(asin=asin, defaults=defaults)

    # Replace the variant tree so re-importing a refreshed scrape stays consistent.
    product.variants.all().delete()
    for vi, v in enumerate(_list(data.get("variants"))):
        variant = Variant.objects.create(
            product=product,
            asin=v.get("asin") or "",
            color=v.get("color") or "",
            style=v.get("style") or "",
            price=v.get("price") or "",
            swatch_image=v.get("swatch_image") or "",
            unavailable=bool(v.get("unavailable")),
            videos=_list(v.get("videos")),
            position=vi,
        )
        imgs = []
        for ii, im in enumerate(_list(v.get("images"))):
            if isinstance(im, str):
                im = {"url": im}
            if not im.get("url"):
                continue
            imgs.append(
                VariantImage(
                    variant=variant,
                    position=im.get("index", ii),
                    slot=im.get("slot") or "",
                    url=im["url"],
                    thumbnail=im.get("thumbnail") or "",
                    full_size=im.get("full_size") or "",
                )
            )
        VariantImage.objects.bulk_create(imgs)
    return created


def import_products(payload) -> ImportResult:
    """payload: JSON string/bytes or already-parsed list/dict."""
    if isinstance(payload, (str, bytes)):
        payload = json.loads(payload)
    items = payload if isinstance(payload, list) else [payload]
    result = ImportResult()
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            result.skipped += 1
            result.errors.append(f"#{i}: not an object")
            continue
        if item.get("error"):
            result.skipped += 1
            result.errors.append(f"#{i} ({item.get('asin')}): scrape error: {item['error']}")
            continue
        try:
            with transaction.atomic():
                created = _import_one(item)
            result.created += created
            result.updated += not created
        except Exception as e:  # keep going; report per item
            result.skipped += 1
            result.errors.append(f"#{i} ({item.get('asin')}): {e}")
    return result

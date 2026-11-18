"""Storefront menu: category -> sub-category -> matching rules.

Sub-categories are NOT stored on the product. A product belongs to a sub-category when its
`category_path` (the scraped breadcrumb) contains one of the `path` words, or — for groups the
breadcrumb can't express, like luxury or travel bags — its title / brand matches. One product can
therefore appear in several sub-categories (e.g. a pullover is in both "Sweaters" and "Pullovers").

Keep the slugs in sync with mallzo/lib/taxonomy.ts.
"""
from django.db.models import Q

TAXONOMY = {
    "apparel": {
        "suiting-blazers": {"path": ["suiting", "blazer"]},
        "sweaters-cardigans": {"path": ["sweater", "cardigan"]},
        "tops-tees-blouses": {"path": ["tops, tees", "blouse", "t-shirt", "tank"]},
        "clothing": {"path": ["dress", "coat", "jacket", "jumpsuit", "hoodie", "sweatshirt", "clothing sets", "pants", "skirt", "tracksuit", "sweatsuit"]},
        "pullovers": {"path": ["pullover"]},
    },
    "footwear": {
        "womens-shoes": {"path": ["women > shoes", "women's shoes"]},
        "sneakers-sports": {"path": ["sneaker", "athletic", "running"]},
        "boots": {"path": ["boots"]},
        "heels-pumps": {"path": ["pumps", "heels"], "title": ["heel", "pump", "stiletto"]},
        "flats-loafers": {"path": ["flats", "loafer", "oxford", "moccasin", "mules", "clogs", "slip-ons"], "title": ["loafer", "ballet flat"]},
        "sandals-slippers": {"path": ["sandal", "slipper", "flip flop", "slides"], "title": ["sandal", "slipper", "slide"]},
    },
    "handbags": {
        "tote-shoulder": {"path": ["totes", "shoulder bag", "hobo", "satchel", "top-handle"], "title": ["tote", "shoulder bag", "hobo", "satchel"]},
        "crossbody": {"path": ["crossbody"], "title": ["crossbody", "cross body"]},
        "clutches-wallets": {"path": ["clutch", "evening bag", "wristlet", "coin purse"], "title": ["clutch", "wallet", "wristlet"]},
        "luxury-bags": {
            "brand": ["marc jacobs", "kurt geiger", "coach", "michael kors", "kate spade", "gucci", "prada", "louis vuitton", "fossil", "furla", "tory burch", "longchamp", "juicy couture"],
            "title": ["luxury", "designer", "lambskin"],
        },
        "travel-bags": {"path": ["luggage", "travel"], "title": ["travel", "duffel", "weekender", "luggage"]},
        "backpacks": {"path": ["backpack"], "title": ["backpack"]},
    },
    "beauty-skincare": {
        "skincare": {"path": ["skin care", "skincare", "face"]},
        "makeup": {"path": ["makeup", "lipstick"]},
        "hair-care": {"path": ["hair"]},
        "fragrance": {"path": ["fragrance", "perfume"]},
        "nail-care": {"path": ["nail"]},
        "bath-body": {"path": ["bath & body", "body care", "soap", "lotion"]},
    },
    "health-care": {
        "vitamins-supplements": {"path": ["vitamin", "supplement", "nutrition"]},
        "personal-care": {"path": ["health & personal care", "shave", "deodorant", "feminine"]},
        "oral-care": {"path": ["oral care", "toothbrush", "toothpaste"]},
        "wellness": {"path": ["wellness", "massage", "relaxation"]},
        "medical-first-aid": {"path": ["medical", "first aid", "health care", "thermometer", "monitor"]},
        "fitness-recovery": {"path": ["fitness", "exercise", "yoga", "recovery"]},
    },
    "home-living": {
        "kitchen-dining": {"path": ["kitchen", "dining", "cookware"]},
        "bedding-bath": {"path": ["bedding", "bath", "towel", "pillow", "blanket"]},
        "decor": {"path": ["decor", "wall art", "candle", "vase"]},
        "furniture": {"path": ["furniture"]},
        "storage-organization": {"path": ["storage", "organization"]},
        "lighting": {"path": ["lighting", "lamp"]},
        "garden-outdoor": {"path": ["garden", "outdoor", "patio"]},
    },
}


def row_matches(category, sub, row):
    """Python twin of sub_query() for a values() row, so counts need only one DB query."""
    rule = TAXONOMY.get(category, {}).get(sub)
    if rule is None:
        return False
    path = (row.get("category_path") or "").lower()
    title = ((row.get("title_en") or "") + " " + (row.get("title") or "")).lower()
    brand = (row.get("brand") or "").lower()
    return (
        any(w in path for w in rule.get("path", []))
        or any(w in title for w in rule.get("title", []))
        or any(w in brand for w in rule.get("brand", []))
    )


def sub_query(category, sub):
    """Q for one sub-category, or None if unknown."""
    rule = TAXONOMY.get(category, {}).get(sub)
    if rule is None:
        return None
    q = Q()
    for w in rule.get("path", []):
        q |= Q(category_path__icontains=w)
    for w in rule.get("title", []):
        q |= Q(title_en__icontains=w) | Q(title__icontains=w)
    for w in rule.get("brand", []):
        q |= Q(brand__icontains=w)
    return q

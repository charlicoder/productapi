"""
Management command to seed specific affiliate products data.
"""

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.products.models import Brand, Category, SubCategory, Product


class Command(BaseCommand):
    help = "Seed database with specific affiliate products data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing data...")
            Product.objects.all().delete()
            SubCategory.objects.all().delete()
            Category.objects.all().delete()
            Brand.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Data cleared!"))

        # 1. Create Brands (Standard Model - No Translations)
        brands = self._create_brands()

        # 2. Create Categories (Translatable)
        categories = self._create_categories()

        # 3. Create Products (Translatable + JSON Fields)
        self._create_products(brands, categories)

        self.stdout.write(self.style.SUCCESS("Successfully seeded database!"))

    def _create_brands(self):
        brands_data = [
            {
                "name": "Nike",
                "slug": "nike",
                "url": "https://www.nike.com/",
                "logo": "https://www.nike.com/logo.png",
            },
            {
                "name": "Sony",
                "slug": "sony",
                "url": "https://www.sony.com/",
                "logo": "https://www.sony.com/logo.png",
            },
            {
                "name": "Samsung",
                "slug": "samsung",
                "url": "https://www.samsung.com/",
                "logo": "https://www.samsung.com/logo.png",
            },
            {
                "name": "Apple",
                "slug": "apple",
                "url": "https://www.apple.com/",
                "logo": "https://www.apple.com/logo.png",
            },
            {
                "name": "BAGSMART",
                "slug": "bagsmart",
                "url": "https://www.bagsmart.com/",
                "logo": "https://www.bagsmart.com/logo.png",
            },
        ]
        brand_objs = {}
        for data in brands_data:
            obj, _ = Brand.objects.update_or_create(slug=data["slug"], defaults=data)
            brand_objs[data["name"]] = obj
        return brand_objs

    def _create_categories(self):
        categories_map = [
            {
                "slug": "sports-outdoors",
                "icon": "running",
                "translations": {
                    "en": "Sports & Outdoors",
                    "ar": "رياضة وأنشطة خارجية",
                    "fr": "Sports et Plein Air",
                },
            },
            {
                "slug": "electronics",
                "icon": "laptop",
                "translations": {
                    "en": "Electronics",
                    "ar": "إلكترونيات",
                    "fr": "Électronique",
                },
            },
            {
                "slug": "womens-fashion",
                "icon": "dress",
                "translations": {
                    "en": "Women's Fashion",
                    "ar": "أزياء نسائية",
                    "fr": "Mode Femme",
                },
            },
        ]
        cat_objs = {}
        for data in categories_map:
            translations = data.pop("translations")
            obj, _ = Category.objects.get_or_create(slug=data["slug"], defaults=data)
            for lang, name in translations.items():
                obj.set_current_language(lang)
                obj.name = name
                obj.save()
            # Map by English name for lookup during product creation
            cat_objs[translations["en"]] = obj
        return cat_objs

    def _create_products(self, brands, categories):
        products_json = [
            {
                "product_asin": "B0B3XNPMQ8",
                "brand_name": "Nike",
                "cat_name": "Sports & Outdoors",
                "platform": "amazon",
                "product_type": "sports",
                "af_link": "https://www.amazon.com/dp/B0B3XNPMQ8?tag=affiliate-20",
                "rating": "4.4",
                "is_featured": True,
                "price_info": {
                    "price": "$89.97",
                    "regular_price": "$130.00",
                    "cost_savings": 40,
                    "discount_percent": "-31%",
                    "savings_percent": "31%",
                },
                "tags_list": [
                    "Sports",
                    "Running",
                    "Nike",
                    "Shoes",
                    "Athletic",
                    "Training",
                ],
                "features": [
                    {"key": "Material", "value": "Mesh upper"},
                    {"key": "Sole", "value": "Rubber"},
                    {"key": "Closure", "value": "Lace-up"},
                    {"key": "Technology", "value": "Nike React foam"},
                    {"key": "Weight", "value": "283g"},
                ],
                "images": [
                    {
                        "image": "https://m.media-amazon.com/images/I/71jeoX0rMBL._AC_SX695_.jpg",
                        "alt_text": "Nike React Infinity Run Flyknit 3",
                        "is_featured": True,
                        "order": 1,
                    }
                ],
                "meta": {
                    "page_header": "Nike React Infinity Run Flyknit 3",
                    "meta_description": "Nike React Infinity Run Flyknit 3 running shoes with React foam for a smooth ride.",
                    "meta_keywords": "Nike, running shoes, React, Flyknit, athletic",
                },
                "titles": {
                    "en": "Nike React Infinity Run Flyknit 3 Men's Road Running Shoes",
                    "ar": "حذاء الجري نايكي ريأكت إنفينيتي ران فلاينت 3 للرجال",
                    "fr": "Chaussures de course Nike React Infinity Run Flyknit 3 pour homme",
                },
                "descriptions": {
                    "en": "Built for long-distance running, the Nike React Infinity Run 3 provides a smooth, stable ride...",
                    "ar": "صُمم للجري لمسافات طويلة، يوفر نايكي ريأكت إنفينيتي ران 3 ركوبًا سلسًا ومستقرًا...",
                    "fr": "Conçue pour la course longue distance, la Nike React Infinity Run 3 offre une conduite fluide...",
                },
            },
            {
                "product_asin": "B09XS7JWHH",
                "brand_name": "Sony",
                "cat_name": "Electronics",
                "platform": "amazon",
                "product_type": "electronics",
                "af_link": "https://www.amazon.com/dp/B09XS7JWHH?tag=affiliate-20",
                "rating": "4.5",
                "is_featured": False,
                "price_info": {
                    "price": "$328.00",
                    "regular_price": "$399.99",
                    "cost_savings": 72,
                    "discount_percent": "-18%",
                    "savings_percent": "18%",
                },
                "tags_list": [
                    "Electronics",
                    "Headphones",
                    "Sony",
                    "Wireless",
                    "Noise Cancelling",
                    "Bluetooth",
                ],
                "features": [
                    {"key": "Type", "value": "Over-Ear Wireless"},
                    {"key": "Noise Cancellation", "value": "Industry Leading ANC"},
                    {"key": "Battery Life", "value": "Up to 30 hours"},
                ],
                "images": [
                    {
                        "image": "https://m.media-amazon.com/images/I/61vJtKbAssL._AC_SX679_.jpg",
                        "alt_text": "Sony WH-1000XM5 Black",
                        "is_featured": True,
                        "order": 1,
                    }
                ],
                "videos": [
                    {
                        "video": "https://www.amazon.com/sony-xm5-video",
                        "title": "Sony WH-1000XM5 Review",
                        "is_featured": True,
                        "order": 1,
                    }
                ],
                "titles": {
                    "en": "Sony WH-1000XM5 Wireless Headphones",
                    "ar": "سماعات سوني WH-1000XM5 اللاسلكية",
                    "fr": "Casque Sony WH-1000XM5 sans fil",
                },
                "descriptions": {
                    "en": "Experience unparalleled sound quality...",
                    "ar": "استمتع بجودة صوت لا مثيل لها...",
                    "fr": "Découvrez une qualité sonore inégalée...",
                },
            },
            {
                "product_asin": "B0CMDLHGK4",
                "brand_name": "Samsung",
                "cat_name": "Electronics",
                "platform": "amazon",
                "product_type": "electronics",
                "af_link": "https://www.amazon.com/dp/B0CMDLHGK4?tag=affiliate-20",
                "rating": "4.6",
                "is_featured": True,
                "price_info": {
                    "price": "$899.99",
                    "regular_price": "$1199.99",
                    "cost_savings": 300,
                    "discount_percent": "-25%",
                    "savings_percent": "25%",
                },
                "tags_list": ["Electronics", "Smartphones", "Samsung", "Galaxy", "AI"],
                "features": [
                    {"key": "Display", "value": '6.8" Dynamic AMOLED 2X'},
                    {"key": "Chip", "value": "Snapdragon 8 Gen 3"},
                ],
                "images": [
                    {
                        "image": "https://m.media-amazon.com/images/I/71Sa3dqTqzL._AC_SX679_.jpg",
                        "alt_text": "Samsung Galaxy S24 Ultra",
                        "is_featured": True,
                        "order": 1,
                    }
                ],
                "titles": {
                    "en": "Samsung Galaxy S24 Ultra (256GB)",
                    "ar": "سامسونج جالاكسي S24 الترا",
                    "fr": "Samsung Galaxy S24 Ultra (256 Go)",
                },
                "descriptions": {
                    "en": "Galaxy S24 Ultra brings you the ultimate Galaxy experience...",
                    "ar": "يقدم لك جالاكسي S24 الترا...",
                    "fr": "Le Galaxy S24 Ultra vous offre...",
                },
            },
            {
                "product_asin": "B0CHOMQ1LV",
                "brand_name": "Apple",
                "cat_name": "Electronics",
                "platform": "amazon",
                "product_type": "electronics",
                "af_link": "https://www.amazon.com/dp/B0CHOMQ1LV?tag=affiliate-20",
                "rating": "4.8",
                "is_featured": True,
                "price_info": {
                    "price": "$999.00",
                    "regular_price": "$1099.00",
                    "cost_savings": 100,
                    "discount_percent": "-9%",
                    "savings_percent": "9%",
                },
                "tags_list": ["Electronics", "Smartphones", "Apple", "iPhone", "5G"],
                "features": [
                    {"key": "Display", "value": '6.1" Super Retina XDR'},
                    {"key": "Chip", "value": "A17 Pro"},
                ],
                "images": [
                    {
                        "image": "https://m.media-amazon.com/images/I/81SigpJN1KL._AC_SX679_.jpg",
                        "alt_text": "iPhone 15 Pro",
                        "is_featured": True,
                        "order": 1,
                    }
                ],
                "titles": {
                    "en": "Apple iPhone 15 Pro (256GB)",
                    "ar": "آيفون 15 برو من آبل",
                    "fr": "Apple iPhone 15 Pro (256 Go)",
                },
                "descriptions": {
                    "en": "iPhone 15 Pro features a strong and light titanium design...",
                    "ar": "يتميز آيفون 15 برو بتصميم تيتانيوم...",
                    "fr": "L'iPhone 15 Pro présente un design en titane...",
                },
            },
            {
                "product_asin": "B0CS2X23RY",
                "brand_name": "BAGSMART",
                "cat_name": "Women's Fashion",
                "platform": "amazon",
                "product_type": "clothing",
                "af_link": "https://www.amazon.com/dp/B0CS2X23RY?tag=affiliate-20",
                "rating": "4.7",
                "is_featured": True,
                "price_info": {
                    "price": "$26.59",
                    "regular_price": "$31.99",
                    "cost_savings": 5,
                    "discount_percent": "-17%",
                    "savings_percent": "17%",
                },
                "tags_list": [
                    "Women",
                    "Handbags & Wallets",
                    "Totes",
                    "Travel",
                    "Work",
                    "Gym",
                ],
                "features": [
                    {"key": "Fabric type", "value": "Polyester fibre"},
                    {"key": "Care instructions", "value": "Machine Wash"},
                ],
                "images": [
                    {
                        "image": "https://m.media-amazon.com/images/I/51k6GQbjoVL._AC_SY550_.jpg",
                        "alt_text": "BAGSMART Tote Bag",
                        "is_featured": True,
                        "order": 1,
                    }
                ],
                "videos": [
                    {
                        "video": "https://www.amazon.com/f5aae4a0-60e1-484b-8473-802c0e45ca6e",
                        "title": "Overview",
                        "is_featured": True,
                    }
                ],
                "titles": {
                    "en": "BAGSMART Lightweight Puffy Tote Bag",
                    "ar": "حقيبة توت خفيفة الوزن من باجسمارت",
                    "fr": "Sac fourre-tout léger BAGSMART",
                },
                "descriptions": {
                    "en": "This BAGSMART Tote Bag is the perfect companion...",
                    "ar": "حقيبة توت باجسمارت للنساء...",
                    "fr": "Ce sac fourre-tout BAGSMART...",
                },
            },
        ]

        for p_data in products_json:
            titles = p_data.pop("titles")
            descs = p_data.pop("descriptions")
            brand = brands.get(p_data.pop("brand_name"))
            category = categories.get(p_data.pop("cat_name"))
            tags = ", ".join(p_data.pop("tags_list"))

            product, _ = Product.objects.update_or_create(
                product_asin=p_data["product_asin"],
                defaults={
                    **p_data,
                    "brand": brand,
                    "category": category,
                    "tags": tags,
                    "rating": Decimal(p_data["rating"]),
                },
            )

            for lang in ["en", "ar", "fr"]:
                product.set_current_language(lang)
                product.title = titles.get(lang, titles["en"])
                product.description = descs.get(lang, descs["en"])
                product.save()

            # Update slug based on English title
            product.generate_slug()
            product.save(update_fields=["slug"])

            self.stdout.write(f"  Processed Product: {product.product_asin}")

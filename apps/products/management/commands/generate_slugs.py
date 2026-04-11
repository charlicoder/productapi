from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.products.models import Product


class Command(BaseCommand):
    help = 'Generate slugs for products without slugs'

    def handle(self, *args, **options):
        products = Product.objects.filter(slug='')
        count = 0
        
        for product in products:
            title = product.safe_translation_getter('title', any_language=True)
            if title:
                base_slug = slugify(title)
                slug = base_slug
                counter = 1
                
                while Product.objects.filter(slug=slug).exclude(pk=product.pk).exists():
                    slug = f"{base_slug}-{product.product_asin.lower()}"
                    if Product.objects.filter(slug=slug).exclude(pk=product.pk).exists():
                        slug = f"{base_slug}-{counter}"
                        counter += 1
                
                product.slug = slug[:550]
                product.save(update_fields=['slug'])
                count += 1
                self.stdout.write(f"  {product.product_asin}: {product.slug}")
        
        self.stdout.write(self.style.SUCCESS(f'Generated {count} slugs!'))


# python manage.py generate_slugs
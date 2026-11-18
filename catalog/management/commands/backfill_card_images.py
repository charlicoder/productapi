from django.core.management.base import BaseCommand
from django.db.models import Prefetch

from catalog.models import Product, Variant


class Command(BaseCommand):
    help = "Fill Product.card_images for existing products (run once after the migration)."

    def handle(self, *args, **opts):
        qs = Product.objects.prefetch_related(Prefetch("variants", queryset=Variant.objects.prefetch_related("images")))
        n = 0
        for p in qs:
            p.refresh_card_images()
            n += 1
        self.stdout.write(self.style.SUCCESS(f"Updated card_images for {n} products"))

from django.core.management.base import BaseCommand

from catalog.importer import import_products


class Command(BaseCommand):
    help = "Import products from a JSON file (list of products or one product)."

    def add_arguments(self, parser):
        parser.add_argument("files", nargs="+")

    def handle(self, *args, files, **opts):
        for f in files:
            with open(f, "rb") as fh:
                r = import_products(fh.read())
            self.stdout.write(f"{f}: created={r.created} updated={r.updated} skipped={r.skipped}")
            for e in r.errors:
                self.stderr.write("  " + e)

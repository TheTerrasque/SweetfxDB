from django.core.management.base import BaseCommand, CommandError
from sweetfx_database.gamedb.models import PresetScreenshot

class Command(BaseCommand):
    help = 'Optimize uploaded images (png via optipng)'

    def handle(self, *args, **options):
        for s in PresetScreenshot.objects.filter(optimized=False, image__endswith=".png"):
            s.optimize()
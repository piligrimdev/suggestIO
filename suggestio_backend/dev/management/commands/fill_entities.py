from django.core.management import BaseCommand
from  dev.models import Entity

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.stdout.write("Creating entities relation")

        for i in range(5):
            Entity.objects.get_or_create(Name=f"Entity #{i+1}")

        self.stdout.write(self.style.SUCCESS(f"Entities populated"))

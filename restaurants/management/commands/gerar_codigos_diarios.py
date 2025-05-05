from django.core.management.base import BaseCommand
from restaurants.models import Restaurant
from django.utils.crypto import get_random_string
from django.utils.timezone import localdate

class Command(BaseCommand):
    help = "Gera um código diário único para cada restaurante"

    def handle(self, *args, **options):
        hoje = localdate()

        for restaurante in Restaurant.objects.all():
            aleatorio = get_random_string(length=6)
            codigo = f"{restaurante.id}-{hoje.isoformat()}-{aleatorio}"
            restaurante.codigo_diario = codigo
            restaurante.save()
            self.stdout.write(self.style.SUCCESS(
                f"{restaurante.name}: {codigo}"
            ))

        self.stdout.write(self.style.SUCCESS("Códigos atualizados com sucesso."))

from django.core.management.base import BaseCommand

from monitoring.models import Zone

# Real, known landslide-prone locations across the North Eastern Region.
# Coordinates only — rainfall and risk are never hardcoded; they're
# fetched live from Open-Meteo at request time (see services.py).
ZONES = [
    ("Sohra (Cherrapunji)", "Meghalaya", 25.285, 91.7362),
    ("Mangan", "Sikkim", 27.5167, 88.5333),
    ("Aizawl", "Mizoram", 23.7271, 92.7176),
    ("Haflong", "Assam (Dima Hasao)", 25.1667, 93.0167),
    ("Gangtok", "Sikkim", 27.3389, 88.6065),
    ("Ukhrul", "Manipur", 25.0454, 94.3608),
    ("Kohima", "Nagaland", 25.6751, 94.1086),
    ("Along (Aalo)", "Arunachal Pradesh", 28.1667, 94.8),
    ("Itanagar", "Arunachal Pradesh", 27.0844, 93.6053),
]


class Command(BaseCommand):
    help = "Seed the database with real NER landslide-monitoring zones."

    def handle(self, *args, **options):
        created_count = 0
        for name, state, lat, lon in ZONES:
            _, created = Zone.objects.get_or_create(
                name=name, state=state, defaults={"latitude": lat, "longitude": lon}
            )
            created_count += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created_count} new zone(s); {len(ZONES)} defined in total."
            )
        )

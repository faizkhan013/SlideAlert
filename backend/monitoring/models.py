from django.db import models


class Zone(models.Model):
    """A real, named location being monitored for landslide risk."""

    name = models.CharField(max_length=120)
    state = models.CharField(max_length=80)
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["state", "name"]
        unique_together = ("name", "state")

    def __str__(self):
        return f"{self.name}, {self.state}"


class RainfallReading(models.Model):
    """
    A cached daily precipitation figure for a Zone, fetched live from the
    Open-Meteo API. `fetched_at` records when we last pulled this value
    from the upstream API — used to decide whether the cache is stale.
    """

    zone = models.ForeignKey(Zone, related_name="readings", on_delete=models.CASCADE)
    date = models.DateField()
    precipitation_mm = models.FloatField(null=True, blank=True)
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("zone", "date")
        ordering = ["date"]

    def __str__(self):
        return f"{self.zone.name} — {self.date}: {self.precipitation_mm} mm"

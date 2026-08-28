from django.contrib import admin

from .models import RainfallReading, Zone


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "state", "latitude", "longitude", "created_at")
    search_fields = ("name", "state")
    list_filter = ("state",)


@admin.register(RainfallReading)
class RainfallReadingAdmin(admin.ModelAdmin):
    list_display = ("zone", "date", "precipitation_mm", "fetched_at")
    list_filter = ("zone__state", "zone")
    ordering = ("-date",)

from django.urls import path

from .views import (
    AlertListView,
    StatsView,
    ZoneDetailView,
    ZoneListView,
    ZoneRefreshView,
)

urlpatterns = [
    path("zones/", ZoneListView.as_view(), name="zone-list"),
    path("zones/<int:pk>/", ZoneDetailView.as_view(), name="zone-detail"),
    path("zones/<int:pk>/refresh/", ZoneRefreshView.as_view(), name="zone-refresh"),
    path("alerts/", AlertListView.as_view(), name="alert-list"),
    path("stats/", StatsView.as_view(), name="stats"),
]

"""Rutas del proyecto: todas se delegan en la aplicación 'api'."""

from django.urls import include, path

urlpatterns = [
    path("", include("api.urls")),
]
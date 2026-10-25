"""Rutas de la aplicación 'api'."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("healthz", views.healthz, name="healthz"),
    path("api/mensaje", views.api_mensaje, name="api_mensaje"),
    path("api/visitas", views.api_visitas, name="api_visitas"),
    path("api/lugares", views.api_lugares, name="api_lugares"),
    path("api/login", views.api_login, name="api_login"),
]
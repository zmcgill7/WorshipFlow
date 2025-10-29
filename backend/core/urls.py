from django.urls import path
from . import views
urlpatterns = [
    path("analyze/", views.analyzeFiles, name="analyzeFiles"),
]

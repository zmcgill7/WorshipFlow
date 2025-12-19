from django.urls import path
from . import views

urlpatterns = [
    path("analyze/", views.analyzeFiles, name="analyzeFiles"),
    path("history/", views.get_history, name="get_history"),
]

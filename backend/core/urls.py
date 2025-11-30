from django.urls import path
from . import views

urlpatterns = [
    path("analyze/", views.analyzeFiles, name="analyzeFiles"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
]

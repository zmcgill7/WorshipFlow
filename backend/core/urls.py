from django.urls import path
from . import views

urlpatterns = [
    path("analyze/", views.analyzeFiles, name="analyzeFiles"),
    path("history/", views.get_history, name="get_history"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
]

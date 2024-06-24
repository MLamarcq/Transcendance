from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("signup", views.signup, name ="signup"),
    path("signin", views.signin, name="signin"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("statistics/", views.statistics, name="statistics"),
    path("chat/", views.chat, name="chat"),
    path("profil/", views.profil_view, name="profil")
]
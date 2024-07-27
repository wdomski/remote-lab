from django.urls import path

from . import views

app_name = "home"

urlpatterns = [
    path('', views.home, name="home"),
    path('login', views.login, name="login"),
    path('logout', views.logout, name="logout"),
    path('terminal', views.terminal, name="terminal"),
    path('terminal/reset', views.terminal_reset, name="terminal_reset"),
    path('terminal/update', views.terminal_update, name="terminal_update"),
]

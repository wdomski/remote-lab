from django.urls import path

from . import views

app_name = "video"

urlpatterns = [
    path('', views.image, name="home"),
    path('stream', views.stream, name="stream"),
    path('video', views.video, name="video"),
    path('image', views.image, name="image"),
    path('camera', views.camera, name="camera"),
    path('settings', views.settings, name="settings"),
    path('autorefresh', views.autorefresh, name="autorefresh"),
]

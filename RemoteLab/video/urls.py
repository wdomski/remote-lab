from django.urls import path

from . import views

app_name = "video"

urlpatterns = [
    path('', views.image, name="home"),
    path('stream_jpeg', views.stream_jpeg, name="stream_jpeg"),
    path('video_jpeg', views.video_jpeg, name="video_jpeg"),
    path('image', views.image, name="image"),
    path('camera', views.camera, name="camera"),
    path('settings', views.settings, name="settings"),
    path('autorefresh', views.autorefresh, name="autorefresh"),
]

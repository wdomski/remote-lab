from django.urls import path

from . import views

app_name = "boards"

urlpatterns = [
    path('', views.home, name="home"),
    path('reset/<str:id>/', views.reset, name="reset"),
    path('halt/<str:id>/', views.halt, name="halt"),
    path('resume/<str:id>/', views.resume, name="resume"),
    path('restart_debugger/<str:id>/', views.restart_debugger, name="restart_debugger"),
    path('start_debugger/<str:id>/', views.start_debugger, name="start_debugger"),
    path('stop_debugger/<str:id>/', views.stop_debugger, name="stop_debugger"),
    path('serial/<str:id>/', views.serial_console, name="serial_console"),
    path('serial_read_stream/<str:id>/', views.serial_read_stream, name="serial_read_stream"),    
    path('serial_read/<str:id>/', views.serial_read, name="serial_read"),    
    path('serial_write/<str:id>/', views.serial_write, name="serial_write"),    
    path('plot/', views.plot, name="plot"),
]

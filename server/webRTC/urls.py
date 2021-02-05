"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.config, name='config')
Class-based views
    1. Add an import:  from other_app.views import config
    2. Add a URL to urlpatterns:  path('', config.as_view(), name='config')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.camera_jetbot, name="camera_jetbot"),
    path(r'^stream/$', views.stream, name='stream'),
]

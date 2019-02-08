"""oceandb URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from argo import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name="home"),
    path('selection/', views.selection, name="argo"),
    path('argo/', views.argo_upload, name="argo"),
    path('drifters/', views.drifters, name="drifters"),
    path('drifter_info/', views.drifter_info, name="drifter_info"),
    path('session_info/', views.session_info, name="session_info"),
    path('argo/sessions_all/', views.sessions_all, name="sessions_all"),
    path('argo/test/', views.calculation, name="test"),
    path('description/', views.description, name="description"),
    path('methods/', views.methods, name="methods"),
    path('density/', views.calc_density, name="density"),
    path('svel/', views.calc_svel, name="svelocity"),
    path('depth/', views.calc_depth, name="depth"),
]

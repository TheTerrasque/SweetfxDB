from django.conf.urls import url
from sweetfx_database.silly import views


urlpatterns = [
    url(r'^$', views.GameNames.as_view(), name='silly-home'),
    url(r'view/(?P<template>\w+)/$', views.ServeTemplate.as_view(), name="silly-template"),
    url(r'^get/json/$', views.get_gamenames, name='silly-js-gamename'),
]

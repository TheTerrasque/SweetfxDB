from django.conf.urls import url
from sweetfx_database.gamedb import views
from django.contrib.auth.decorators import login_required as li

from . import feeds

urlpatterns = [
    url(r'^$', views.GameList.as_view(), name='g-games-list'),
    url(r'game/(?P<pk>\d+)/$', views.GameDetails.as_view(), name='g-game-detail'),
    url(r'game/(?P<pk>\d+)/new_preset/$', views.AddPreset.as_view(), name='g-game-add-preset'),
    url(r'game/new/$', views.AddGame.as_view(), name='g-game-add'),
    url(r'game/search/$', views.search, name='g-game-search'),
    url(r'game/(?P<pk>\d+)/edit/$', views.EditGame.as_view(), name='g-game-edit'),

    url(r'preset/(?P<pk>\d+)/$', views.PresetDetails.as_view(), name='g-preset-detail'),
    url(r'preset/(?P<pk>\d+)/add_screenshot/$', views.AddScreenshot.as_view(), name='g-preset-add-screenshot'),
    url(r'preset/(?P<pk>\d+)/edit/$', views.EditPreset.as_view(), name='g-preset-edit'),
    url(r'preset/(?P<pk>\d+)/download/$', views.download_preset, name='g-preset-download'),
    url(r'preset/newlist/$', views.LatestPresets.as_view(), name='g-preset-new-list'),
    url(r'preset/popularlist/$', views.PopularPresets.as_view(), name='g-preset-popular-list'),

    url(r'shader/$', views.ShaderList.as_view(), name='g-shader-list'),
    url(r'shader/(?P<pk>\d+)/$', views.ShaderDetails.as_view(), name='g-shader-detail'),

    url(r'screenshot/(?P<pk>\d+)/$', views.ScreenshotDetails.as_view(), name='g-screenshot-detail'),
    url(r'screenshot/(?P<pk>\d+)/edit/$', views.EditScreenshot.as_view(), name='g-screenshot-edit'),
    url(r'screenshot/(?P<pk>\d+)/full/$', views.ScreenshotFull.as_view(), name='g-screenshot-full'),

    url(r'comment/new/$', views.save_comment, name="g-save-comment"),

    url(r'view/(?P<template>\w+)/$', views.ServeTemplate.as_view(), name="g-show-template"),

    url(r'rss/$', feeds.LatestPresetsFeed(), name="g-feed-presets"),
]

# from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path('subscriptions/', views.subscriptions, name='index'),
    path('favorite/', views.favorite, name='favorite'),
    path('shopping_cart', views.shopping_cart, name='shopping_cart'),
]

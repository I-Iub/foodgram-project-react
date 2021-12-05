from django.urls import path

from .views import login, logout

urlpatterns = [
    path('auth/token/login/', login),
    path('auth/token/logout/', logout)
]

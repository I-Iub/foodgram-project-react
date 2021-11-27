from django.urls import include, path

from .views import login, logout

urlpatterns = [
    # path('auth/', include('djoser.urls')),
    # path('auth/', include('djoser.urls.jwt')),
    path('auth/token/login/', login),
    path('auth/token/logout/', logout)
]

from django.urls import path

from users.views import login, logout

urlpatterns = [
    path('auth/token/login/', login, name='login'),
    path('auth/token/logout/', logout, name='logout')
]

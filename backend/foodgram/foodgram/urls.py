from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('users/', include('users.urls', namespace='users')),
    path('api/', include('api.urls')),
    path('api/', include('users.urls')),
    path('', include('organizer.urls')),
    path('', include('recipes.urls')),
]

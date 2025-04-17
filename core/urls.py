from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView

urlpatterns = [
    # Admin com logout customizado
    
    
    path('admin/', admin.site.urls),
    
    # Sistema de autenticação completo

    
    # ... outras URLs do seu projeto ...
]
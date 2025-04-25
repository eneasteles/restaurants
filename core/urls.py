from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView

from core.api import api




admin.site.site_header = "Administração de Restaurantes"
admin.site.site_title = "Painel Admin do Restaurantes"
admin.site.index_title = "Gerenciar Conteúdo do Restaurantes"
urlpatterns = [
    # Admin com logout customizado
    
    
    
    path('cashier/', include('cashier.urls')),    
    path('restaurants/', include('restaurants.urls')),  # <-- ADICIONE ESTA LINHA
    path("api/", api.urls),
    path('', admin.site.urls),
    
    # Sistema de autenticação completo

    
    # ... outras URLs do seu projeto ...
]
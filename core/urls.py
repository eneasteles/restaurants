from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView


admin.site.site_header = "Administração de Restaurantes"
admin.site.site_title = "Painel Admin do Restaurantes"
admin.site.index_title = "Gerenciar Conteúdo do Restaurantes"
urlpatterns = [
    # Admin com logout customizado
    
    
    path('', admin.site.urls),
    path('cashier/', include('cashier.urls')),
    path('restaurants/', include('restaurants.urls')),
    
    # Sistema de autenticação completo

    
    # ... outras URLs do seu projeto ...
]
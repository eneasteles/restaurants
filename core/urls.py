from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
from restaurants import views
from core.api import api




admin.site.site_header = "Administração de Restaurantes"
admin.site.site_title = "Painel Admin do Restaurantes"
admin.site.index_title = "Gerenciar Conteúdo do Restaurantes"







urlpatterns = [
    # Admin com logout customizado
    
    
    
    path('cashier/', include('cashier.urls')),    
    path('', include('restaurants.urls')),  # <-- ADICIONE ESTA LINHA
    path("api/", api.urls),
    path('admin/', admin.site.urls),
    path('cupom/<int:payment_id>/', views.gerar_cupom_pdf, name='gerar_cupom'),
    
    # Sistema de autenticação completo

    
    # ... outras URLs do seu projeto ...
]
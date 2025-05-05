from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
from restaurants import views
#from core.api import api


from ninja import NinjaAPI
from restaurants.api import kitchen_router
from restaurants.cards_api import card_router 
from restaurants.menu_api import menu_router

api = NinjaAPI()


api.add_router("/", menu_router)


api.add_router("/", kitchen_router)
api.add_router("/", card_router) 




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
    path('fiscal/', include('fiscal.urls')),
    

    
    # Sistema de autenticação completo

    
    # ... outras URLs do seu projeto ...
]



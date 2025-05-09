from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
from restaurants import views
#from core.api import api
from ninja import NinjaAPI
#from restaurants.api import kitchen_router
#from restaurants.cards_api import card_router 
from restaurants.menu_api import menu_router
#from restaurants.payments_api import payment_router

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
api = NinjaAPI()




# restaurants/api_unificado.py







admin.site.site_header = "Administração de Restaurantes"
admin.site.site_title = "Painel Admin do Restaurantes"
admin.site.index_title = "Gerenciar Conteúdo do Restaurantes"

urlpatterns = [
    # Admin com logout customizado 
    path('cashier/', include('cashier.urls')),    
    path('', include('restaurants.urls')),  # <-- ADICIONE ESTA LINHA
    path("api/", include('api.urls')),
    path('admin/', admin.site.urls),
    path('cupom/<int:payment_id>/', views.gerar_cupom_pdf, name='gerar_cupom'),
    path('fiscal/', include('fiscal.urls')),
    
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),    
    # ... outras URLs do seu projeto ...
]



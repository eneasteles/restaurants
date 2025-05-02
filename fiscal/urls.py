# fiscal/urls.py
from django.urls import path
from . import views
from fiscal import views as fiscal_views
urlpatterns = [
    path('emitir-nfce/<int:pk>/', views.emitir_nfce, name='emitir_nfce'),
    path('admin/emitir-nfce/<int:pk>/', fiscal_views.emitir_nfce, name='emitir_nfce'),
]

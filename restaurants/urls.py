from django.urls import path
from . import views

app_name = 'restaurants'

# restaurante_saas/urls.py ou restaurants/urls.py
from django.contrib import admin
from django.urls import path
from core.api import api  # importa o objeto da API do Django Ninja



urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Restaurantes
    path('restaurant/add/', views.RestaurantCreateView.as_view(), name='restaurant_add'),
    path('restaurant/<int:pk>/edit/', views.RestaurantUpdateView.as_view(), name='restaurant_edit'),
    path('restaurant/list/', views.RestaurantListView.as_view(), name='restaurant_list'),
    
    # Mesas
    path('restaurant/<int:restaurant_id>/tables/', views.TableListView.as_view(), name='table_list'),
    path('restaurant/<int:restaurant_id>/tables/add/', views.TableCreateView.as_view(), name='table_add'),
    
    # Cardápio
    path('restaurant/<int:restaurant_id>/menu/add/', views.MenuItemCreateView.as_view(), name='menuitem_add'),
    
    # Pedidos
    path('restaurant/<int:restaurant_id>/orders/add/', views.OrderCreateView.as_view(), name='order_add'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),



]
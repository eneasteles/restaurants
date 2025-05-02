# restaurants/urls.py
from django.urls import path
from . import views



app_name = 'restaurants'


from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, get_object_or_404
from .models import CardItem

@staff_member_required
def marcar_pronto_view(request, pk):
    item = get_object_or_404(CardItem, pk=pk)
    item.is_ready = True
    item.save()
    return redirect('/admin/restaurants/carditem/')


urlpatterns = [
    # home
    path('', views.home, name='home'),
    path('admin/marcar_pronto/<int:pk>/', marcar_pronto_view, name='marcar_pronto'),
    
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # Restaurante
    path('restaurant/add/', views.RestaurantCreateView.as_view(), name='restaurant_add'),
    path('restaurant/<int:pk>/edit/', views.RestaurantUpdateView.as_view(), name='restaurant_edit'),
    path('restaurant/list/', views.RestaurantListView.as_view(), name='restaurant_list'),

    # Mesa
    path('restaurant/<int:restaurant_id>/tables/', views.TableListView.as_view(), name='table_list'),
    path('restaurant/<int:restaurant_id>/tables/add/', views.TableCreateView.as_view(), name='table_add'),

    # Cardápio
    path('restaurant/<int:restaurant_id>/menu/add/', views.MenuItemCreateView.as_view(), name='menuitem_add'),

    # Pedidos
    path('restaurant/<int:restaurant_id>/orders/add/', views.OrderCreateView.as_view(), name='order_add'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),

    # RELATÓRIO Recebimentos
    path('restaurants/relatorio-recebimentos/', views.relatorio_recebimentos, name='relatorio-recebimentos'),
]

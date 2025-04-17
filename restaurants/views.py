from django.views.generic import CreateView, UpdateView, ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.contrib import messages
from .models import Restaurant, Table, Category, MenuItem, Order, Customer,Payment
from .forms import RestaurantForm, TableForm, MenuItemForm, OrderForm, CustomerForm
from django.contrib.auth import views as auth_views

# restaurants/views.py (adicionar isso)


from .forms import PaymentForm

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'restaurants/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['restaurants'] = Restaurant.objects.filter(owner=self.request.user)
        return context

class RestaurantCreateView(LoginRequiredMixin, CreateView):
    model = Restaurant
    form_class = RestaurantForm
    template_name = 'restaurants/restaurant_form.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Restaurante criado com sucesso!')
        return super().form_valid(form)

class RestaurantUpdateView(LoginRequiredMixin, UpdateView):
    model = Restaurant
    form_class = RestaurantForm
    template_name = 'restaurants/restaurant_form.html'
    success_url = reverse_lazy('dashboard')

    def get_queryset(self):
        return Restaurant.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Restaurante atualizado com sucesso!')
        return super().form_valid(form)

class RestaurantListView(LoginRequiredMixin, ListView):
    model = Restaurant
    template_name = 'restaurants/restaurant_list.html'
    
    def get_queryset(self):
        return Restaurant.objects.filter(owner=self.request.user)

class TableCreateView(LoginRequiredMixin, CreateView):
    model = Table
    form_class = TableForm
    template_name = 'restaurants/table_form.html'

    def get_success_url(self):
        return reverse_lazy('table_list', kwargs={'restaurant_id': self.object.restaurant.id})

    def form_valid(self, form):
        restaurant = get_object_or_404(Restaurant, pk=self.kwargs['restaurant_id'], owner=self.request.user)
        form.instance.restaurant = restaurant
        messages.success(self.request, 'Mesa adicionada com sucesso!')
        return super().form_valid(form)

class TableListView(LoginRequiredMixin, ListView):
    model = Table
    template_name = 'restaurants/table_list.html'
    
    def get_queryset(self):
        restaurant = get_object_or_404(Restaurant, pk=self.kwargs['restaurant_id'], owner=self.request.user)
        return Table.objects.filter(restaurant=restaurant)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['restaurant'] = get_object_or_404(Restaurant, pk=self.kwargs['restaurant_id'])
        return context

class MenuItemCreateView(LoginRequiredMixin, CreateView):
    model = MenuItem
    form_class = MenuItemForm
    template_name = 'restaurants/menuitem_form.html'
    
    def get_success_url(self):
        return reverse_lazy('menu_list', kwargs={'restaurant_id': self.object.restaurant.id})

    def form_valid(self, form):
        restaurant = get_object_or_404(Restaurant, pk=self.kwargs['restaurant_id'], owner=self.request.user)
        form.instance.restaurant = restaurant
        messages.success(self.request, 'Item adicionado ao cardápio!')
        return super().form_valid(form)

class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'restaurants/order_form.html'

    def get_success_url(self):
        return reverse_lazy('order_detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['restaurant_id'] = self.kwargs['restaurant_id']
        return kwargs

    def form_valid(self, form):
        restaurant = get_object_or_404(Restaurant, pk=self.kwargs['restaurant_id'], owner=self.request.user)
        form.instance.restaurant = restaurant
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        if form.instance.table:
            form.instance.table.is_occupied = True
            form.instance.table.save()
            
        messages.success(self.request, 'Pedido criado com sucesso!')
        return response

class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'restaurants/order_detail.html'

    def get_queryset(self):
        return Order.objects.filter(restaurant__owner=self.request.user)



class PaymentCreateView(CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = "restaurants/payment_form.html"

    def form_valid(self, form):
        order = get_object_or_404(Order, pk=self.kwargs["order_id"])
        form.instance.order = order
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("order_detail", kwargs={"pk": self.object.order.id})
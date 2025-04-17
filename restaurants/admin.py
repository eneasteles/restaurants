from django.contrib import admin
from .models import Restaurant, Table, Category, MenuItem, Order, OrderItem, Customer
from .models import PaymentMethod, Payment

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('menu_item', 'quantity', 'price', 'subtotal')
    readonly_fields = ('subtotal',)
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.base_fields['price'].initial = None  # Forçar uso do preço do item
        return formset
    
    def subtotal(self, instance):
        return f"R$ {instance.subtotal():.2f}"
    subtotal.short_description = ('Subtotal')

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'phone', 'email', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'owner__username', 'phone')
    prepopulated_fields = {'slug': ('name',)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Superusuário vê tudo
        if request.user.is_superuser:
            return qs
        # Dono vê só suas mesas
        return qs.filter(restaurante__owner=request.user)

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', 'restaurant', 'capacity', 'is_occupied')
    list_filter = ('restaurant', 'is_occupied')
    search_fields = ('number', 'restaurant__name')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'order')
    list_filter = ('restaurant',)
    ordering = ('restaurant', 'order')
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Superusuário vê tudo
        if request.user.is_superuser:
            return qs
        # Dono vê só suas mesas
        return qs.filter(restaurant__owner=request.user)

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Superusuário vê tudo
        if request.user.is_superuser:
            return qs
        # Dono vê só suas mesas
        return qs.filter(restaurant__owner=request.user)
    list_display = ('name', 'category', 'price', 'is_available')
    list_filter = ('restaurant', 'category', 'is_available')
    search_fields = ('name', 'description')
    list_editable = ('price', 'is_available')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Superusuário vê tudo
        if request.user.is_superuser:
            return qs
        # Dono vê só suas mesas
        return qs.filter(restaurant__owner=request.user)
    list_display = ('id', 'restaurant', 'table', 'status', 'created_at', 'total_display')
    readonly_fields = ('total_display',)
    
    def total_display(self, obj):
        total = sum(item.subtotal() for item in obj.order_items.all())
        return f"R$ {total:.2f}"
    total_display.short_description = ('Total')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):    
    list_display = ('name', 'restaurant', 'phone', 'email')
    search_fields = ('name', 'phone', 'email')
    list_filter = ('restaurant',)
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Superusuário vê tudo
        if request.user.is_superuser:
            return qs
        # Dono vê só suas mesas
        return qs.filter(restaurant__owner=request.user)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'menu_item', 'quantity', 'price', 'subtotal_display')
    list_filter = ('order__restaurant',)
    
    
    def subtotal_display(self, obj):
        return f"R$ {obj.subtotal():.2f}"
    subtotal_display.short_description = 'Subtotal'

# restaurants/admin.py



@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "needs_change"]

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "method", "amount", "created_at"]
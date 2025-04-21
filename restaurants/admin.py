from django.contrib import admin
from .models import Restaurant, Table, Category, MenuItem, Order, OrderItem, Customer


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('menu_item', 'quantity', 'price', 'subtotal')
    readonly_fields = ('subtotal',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "menu_item" and not request.user.is_superuser:
            kwargs["queryset"] = MenuItem.objects.filter(restaurant__owner=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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
        return qs.filter(owner=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "restaurant":
                kwargs["queryset"] = Restaurant.objects.filter(owner=request.user)
            elif db_field.name == "table":
                kwargs["queryset"] = Table.objects.filter(restaurant__owner=request.user)
            elif db_field.name == "customer":
                kwargs["queryset"] = Customer.objects.filter(restaurant__owner=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not request.user.is_superuser:
            fields = [f for f in fields if f != 'restaurant']
        return fields
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.owner = request.user
        super().save_model(request, obj, form, change)

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', 'restaurant', 'capacity', 'is_occupied')
    list_filter = ('restaurant', 'is_occupied')
    search_fields = ('number', 'restaurant__name')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(restaurant__owner=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser and db_field.name == "restaurant":
            kwargs["queryset"] = Restaurant.objects.filter(owner=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not request.user.is_superuser:
            fields = [f for f in fields if f != 'restaurant']
        return fields

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser and not obj.restaurant_id:
            obj.restaurant = Restaurant.objects.filter(owner=request.user).first()
        super().save_model(request, obj, form, change)
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
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "restaurant":
                kwargs["queryset"] = Restaurant.objects.filter(owner=request.user)
            elif db_field.name == "table":
                kwargs["queryset"] = Table.objects.filter(restaurant__owner=request.user)
            elif db_field.name == "customer":
                kwargs["queryset"] = Customer.objects.filter(restaurant__owner=request.user)
            elif db_field.name == "categoria":
                kwargs["queryset"] = Category.objects.filter(restaurant__owner=request.user)    
            
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not request.user.is_superuser:
            fields = [f for f in fields if f != 'restaurant']
        return fields
    
    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser and not obj.restaurant_id:
            obj.restaurant = Restaurant.objects.filter(owner=request.user).first()
        super().save_model(request, obj, form, change)

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Superusuário vê tudo
        if request.user.is_superuser:
            return qs
        # Dono vê só suas mesas
        return qs.filter(restaurant__owner=request.user)
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "restaurant":
                kwargs["queryset"] = Restaurant.objects.filter(owner=request.user)
            elif db_field.name == "table":
                kwargs["queryset"] = Table.objects.filter(restaurant__owner=request.user)
            elif db_field.name == "customer":
                kwargs["queryset"] = Customer.objects.filter(restaurant__owner=request.user)
            elif db_field.name == "categoria":
                kwargs["queryset"] = Category.objects.filter(restaurant__owner=request.user)  
            elif db_field.name == "menu_item":
                kwargs["queryset"] = MenuItem.objects.filter(restaurant__owner=request.user)  
            
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    list_display = ('name', 'category', 'price', 'is_available')
    list_filter = ('restaurant', 'category', 'is_available')
    search_fields = ('name', 'description')
    list_editable = ('price', 'is_available')

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not request.user.is_superuser:
            fields = [f for f in fields if f != 'restaurant']
        return fields
    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser and not obj.restaurant_id:
            obj.restaurant = Restaurant.objects.filter(owner=request.user).first()
        super().save_model(request, obj, form, change)

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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "restaurant":
                kwargs["queryset"] = Restaurant.objects.filter(owner=request.user)
            elif db_field.name == "table":
                kwargs["queryset"] = Table.objects.filter(restaurant__owner=request.user)
            elif db_field.name == "customer":
                kwargs["queryset"] = Customer.objects.filter(restaurant__owner=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def total_display(self, obj):
        total = sum(item.subtotal() for item in obj.order_items.all())
        return f"R$ {total:.2f}"
    total_display.short_description = ('Total')

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not request.user.is_superuser:
            fields = [f for f in fields if f != 'restaurant']
        return fields

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser and not obj.restaurant_id:
            obj.restaurant = Restaurant.objects.filter(owner=request.user).first()
        super().save_model(request, obj, form, change)

    inlines = [OrderItemInline]     

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
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "restaurant":
                kwargs["queryset"] = Restaurant.objects.filter(owner=request.user)
            elif db_field.name == "table":
                kwargs["queryset"] = Table.objects.filter(restaurant__owner=request.user)
            elif db_field.name == "customer":
                kwargs["queryset"] = Customer.objects.filter(restaurant__owner=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not request.user.is_superuser:
            fields = [f for f in fields if f != 'restaurant']
        return fields

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser and not obj.restaurant_id:
            obj.restaurant = Restaurant.objects.filter(owner=request.user).first()
        super().save_model(request, obj, form, change)




# restaurants/admin.py



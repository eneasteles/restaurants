from django.contrib import admin
from .models import Restaurant, Table, Category, MenuItem, Order, OrderItem, Customer, Card, CardItem
from django.utils.timezone import localdate


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
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
    list_display = ('id', 'restaurant',  'table', 'status', 'created_at', 'total_display')
    readonly_fields = ('total_display',)
    


    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "restaurant":
                kwargs["queryset"] = Restaurant.objects.filter(owner=request.user)
            elif db_field.name == "table":
                kwargs["queryset"] = Table.objects.filter(restaurant__owner=request.user)
            elif db_field.name == "customer":
                kwargs["queryset"] = Customer.objects.filter(restaurant__owner=request.user)
            elif db_field.name == "card":
                kwargs["queryset"] = Card.objects.filter(restaurant__owner=request.user)
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

class CardItemInline(admin.TabularInline):
    model = CardItem
    extra = 1
    fields = ('card','menu_item', 'quantity', 'price', 'subtotal')
    readonly_fields = ('subtotal',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "menu_item" and not request.user.is_superuser:
            kwargs["queryset"] = MenuItem.objects.filter(restaurant__owner=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def subtotal(self, instance):
        return f"R$ {instance.subtotal():.2f}"
    subtotal.short_description = ('Subtotal')

class DisponibilidadeCartaoFilter(admin.SimpleListFilter):
    title = 'Disponibilidade'
    parameter_name = 'disponivel'

    def lookups(self, request, model_admin):
        return (
            ('livre', 'Disponível para uso'),
            ('pago', 'Já pago hoje'),
        )

    def queryset(self, request, queryset):
        today = localdate()
        pagos_hoje = CardPayment.objects.filter(
            paid_at__date=today
        ).values_list('card_id', flat=True)

        if self.value() == 'livre':
            return queryset.exclude(id__in=pagos_hoje)
        if self.value() == 'pago':
            return queryset.filter(id__in=pagos_hoje)
        return queryset



@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('id', 'number', 'is_active', 'total_display', 'status_display')
    list_filter = ('number', 'is_active', DisponibilidadeCartaoFilter)
    readonly_fields = ('total_display',)

    def status_display(self, obj):
        return "Pago hoje" if obj.was_paid_today else "Disponível"
    status_display.short_description = "Status do dia"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(restaurant__owner=request.user)
    
    def total_display(self, obj):
        total = sum(item.subtotal() for item in obj.card_items.all())
        return f"R$ {total:.2f}"
    total_display.short_description = ('Total')

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser and not obj.restaurant_id:
            obj.restaurant = Restaurant.objects.filter(owner=request.user).first()
        super().save_model(request, obj, form, change)

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not request.user.is_superuser:
            fields = [f for f in fields if f != 'restaurant']
        return fields
    
    list_filter = ('number', 'is_active', DisponibilidadeCartaoFilter)
    inlines = [CardItemInline]




from django.contrib import admin
from .models import CardPayment, Restaurant, Card

@admin.register(CardPayment)
class CardPaymentAdmin(admin.ModelAdmin):
    list_display = ('card', 'restaurant', 'amount', 'payment_method', 'paid_at')
    list_filter = ('payment_method', 'paid_at')
    search_fields = ('card__number', 'restaurant__name')
    readonly_fields = ('paid_at',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(restaurant__owner=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "restaurant":
                kwargs["queryset"] = Restaurant.objects.filter(owner=request.user)
            elif db_field.name == "card":
                # Filtra cartões ativos e sem pagamento feito hoje
                pagos_hoje = CardPayment.objects.filter(
                    restaurant__owner=request.user,
                    paid_at__date=localdate()
                ).values_list('card_id', flat=True)

                kwargs["queryset"] = Card.objects.filter(
                    restaurant__owner=request.user,
                    is_active=True
                ).exclude(id__in=pagos_hoje)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not request.user.is_superuser:
            return [f for f in fields if f != 'restaurant']
        return fields

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser and not obj.restaurant_id:
            obj.restaurant = Restaurant.objects.filter(owner=request.user).first()
        super().save_model(request, obj, form, change)

        # Desativar o cartão depois de salvar o pagamento
        if obj.card and obj.card.is_active:
            obj.card.is_active = False
            obj.card.save()

 
 # restaurants/admin.py



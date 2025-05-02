from django.utils.safestring import mark_safe

from django.contrib import admin
from .models import Restaurant, Table, Category, MenuItem, Order, OrderItem, Customer, Card, CardItem, Stock,CardPayment
from django.utils.timezone import localdate

import qrcode
import base64
from io import BytesIO

import uuid

from django import forms
from .models import MenuItem

from django.utils.html import format_html
from django.urls import reverse

from django.urls import reverse
from django.utils.html import format_html
from django.contrib import messages
from fiscal.models import NotaFiscal

class MenuItemWithStockLabelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        try:
            stock = obj.stock.quantity
        except:
            stock = 0
        return f"{obj.name} (Estoque: {stock})"

def gerar_payload_pix(chave_pix: str, valor: float, nome_recebedor: str, cidade: str, txid: str = None) -> str:
    valor_str = f"{valor:.2f}"

    if not txid:
        # Gera um txid automático se não receber
        txid = uuid.uuid4().hex[:6].upper()  # 6 caracteres aleatórios

    gui = "BR.GOV.BCB.PIX"
    merchant_info = f"00{len(gui):02d}{gui}" + f"01{len(chave_pix):02d}{chave_pix}"
    merchant_info_formatado = f"26{len(merchant_info):02d}{merchant_info}"

    info_adicional = f"05{len(txid):02d}{txid}"
    info_adicional_formatado = f"62{len(info_adicional):02d}{info_adicional}"

    payload_sem_crc = (
        "000201"
        + merchant_info_formatado
        + "52040000"
        + "5303986"
        + f"54{len(valor_str):02d}{valor_str}"
        + "5802BR"
        + f"59{len(nome_recebedor):02d}{nome_recebedor}"
        + f"60{len(cidade):02d}{cidade}"
        + info_adicional_formatado
        + "6304"
    )

    crc16 = calcular_crc16(payload_sem_crc)
    payload_completo = payload_sem_crc + crc16
    return payload_completo


def calcular_crc16(payload):
    polinomio = 0x1021
    resultado = 0xFFFF

    for caractere in payload:
        resultado ^= ord(caractere) << 8
        for _ in range(8):
            if (resultado & 0x8000) != 0:
                resultado = (resultado << 1) ^ polinomio
            else:
                resultado <<= 1
            resultado &= 0xFFFF

    return f"{resultado:04X}"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ('menu_item', 'quantity', 'price', 'subtotal')
    readonly_fields = ('subtotal',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "menu_item" and not request.user.is_superuser:
            kwargs["queryset"] = MenuItem.objects.filter(restaurant__owner=request.user)
            return MenuItemWithStockLabelChoiceField(queryset=kwargs["queryset"])
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
            restaurant = Restaurant.objects.filter(owner=request.user).first()
            if not restaurant:
                raise ValueError("Usuário não possui restaurante cadastrado.")
            obj.restaurant = restaurant
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
            elif db_field.name == "category":
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
            return MenuItemWithStockLabelChoiceField(queryset=kwargs["queryset"])
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






@admin.register(CardPayment)
class CardPaymentAdmin(admin.ModelAdmin):
    list_display = ('id','restaurant','card', 'amount', 'payment_method', 'paid_amount', 'change_amount',  'cupom_link', 'nota_fiscal_emitida', 'emitir_nfce_link','paid_at')
    list_filter = ('payment_method', 'paid_at')
    search_fields = ('card__number', 'restaurant__name')
    readonly_fields = ('amount', 'change_amount', 'paid_at','qrcode_pix')
    
    def nota_fiscal_emitida(self, obj):
        return hasattr(obj, 'nota_fiscal')
    nota_fiscal_emitida.boolean = True
    nota_fiscal_emitida.short_description = "NFC-e Emitida?"

    def emitir_nfce_link(self, obj):
        if hasattr(obj, 'nota_fiscal'):
            return format_html('<a href="{}" target="_blank">Ver NFC-e</a>',
                reverse('admin:fiscal_notafiscal_change', args=[obj.nota_fiscal.id])
            )
        return format_html(
            '<a class="button" href="{}">Emitir NFC-e</a>',
            reverse('emitir_nfce', args=[obj.pk])
        )
    emitir_nfce_link.short_description = "Emitir o NFC-e"
    
    def cupom_link(self, obj):
        url = reverse('gerar_cupom', args=[obj.id])
        return format_html('<a class="button" href="{}" target="_blank">CUPOM DE VENDA</a>', url)
    cupom_link.short_description = "EMITIR CUPOM DE VENDA"
    cupom_link.allow_tags = True

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not request.user.is_superuser:
            fields = [f for f in fields if f != 'restaurant']

        # Adiciona o qrcode_pix manualmente no form
        if 'qrcode_pix' not in fields:
            fields.append('qrcode_pix')

        return fields



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

    def qrcode_pix(self, obj):
        if obj.payment_method != obj.PaymentMethod.PIX:
            return "Forma de pagamento não é Pix."

        if not obj.restaurant.chave_pix:
            return "Restaurante sem chave Pix cadastrada."
        
        txid = f"CARD{obj.card.number:04d}"  # Exemplo: cartão 23 vira "CARD0023"

        # Gerar Payload Pix
        payload = gerar_payload_pix(
            chave_pix=obj.restaurant.chave_pix,  # <- CORRETO AGORA
            valor=float(obj.amount),
            #nome_recebedor=obj.restaurant.name[:25],  # Máximo 25 caracteres
            nome_recebedor="ENEAS BEZERRA TELES",
            cidade="Fortaleza",
            txid=txid
        )

        # Gerar QR Code
        qr = qrcode.make(payload)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        img_html = f'<img src="data:image/png;base64,{img_base64}" width="300" height="300" />'
        return mark_safe(img_html)


    qrcode_pix.short_description = "QR Code Pix"
 # restaurants/admin.py


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('menu_item_name', 'quantity')
    search_fields = ('menu_item__name',)
    actions = ['repor_estoque']
    #########################
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
            elif db_field.name == "stock":
                kwargs["queryset"] = Stock.objects.filter(restaurant__owner=request.user)
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

    ####################

    def menu_item_name(self, obj):
        return obj.menu_item.name
    menu_item_name.short_description = 'Item do Menu'

    def restaurant_name(self, obj):
        return obj.restaurant.name
    restaurant_name.short_description = 'Restaurante'

    @admin.action(description='Repor 10 unidades selecionadas')
    def repor_estoque(self, request, queryset):
        for stock in queryset:
            stock.quantity += 10
            stock.save()
        self.message_user(request, "Reposição concluída com sucesso!")

from .models import StockEntry, StockEntryItem

class StockEntryItemInline(admin.TabularInline):
    model = StockEntryItem
    extra = 1

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Garante que só itens do restaurante certo aparecem"""
        if db_field.name == "menu_item" and not request.user.is_superuser:
            # Se estiver editando uma nota, limitar os itens ao restaurante dela
            parent_id = request.resolver_match.kwargs.get('object_id')
            if parent_id:
                try:
                    stock_entry = StockEntry.objects.get(pk=parent_id)
                    kwargs["queryset"] = MenuItem.objects.filter(restaurant=stock_entry.restaurant)
                except StockEntry.DoesNotExist:
                    kwargs["queryset"] = MenuItem.objects.none()
            else:
                kwargs["queryset"] = MenuItem.objects.filter(restaurant__owner=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)



@admin.register(StockEntry)
class StockEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'restaurant', 'created_at', 'supplier')
    search_fields = ('restaurant__name', 'supplier')
    list_filter = ('restaurant', 'created_at')
    date_hierarchy = 'created_at'
    inlines = [StockEntryItemInline]
    exclude = ('restaurant',)  # <-- OCULTA o campo no admin!

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(restaurant__owner=request.user)

    def save_model(self, request, obj, form, change):
        """Define automaticamente o restaurante na criação"""
        if not obj.pk:  # Só na criação
            obj.restaurant = Restaurant.objects.get(owner=request.user)
        super().save_model(request, obj, form, change)



from django.contrib import admin
from .models import CardItem

@admin.register(CardItem)
class CardItemCozinhaAdmin(admin.ModelAdmin):
    list_display = ('card_number', 'menu_item', 'quantity', 'is_ready', 'marcar_pronto_link')
    list_filter = ('card__number',)  # Filtro por número da comanda
    readonly_fields = ('card', 'menu_item', 'quantity')
    ordering = ('card__number', 'menu_item__name')  # Ordenação por comanda

    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False
    def has_change_permission(self, request, obj=None): return True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs.filter(is_ready=False).select_related('card', 'menu_item')
        return qs.filter(
            is_ready=False,
            card__restaurant__owner=request.user
        ).select_related('card', 'menu_item')


    def card_number(self, obj):
        return f"Comanda {obj.card.number}"
    card_number.short_description = "Comanda"

    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context['refresh_interval'] = 10  # segundos
        return super().changelist_view(request, extra_context=extra_context)


    def marcar_pronto_link(self, obj):
        if not obj.is_ready:
            return mark_safe(f'<a class="button" href="/admin/marcar_pronto/{obj.pk}/">Marcar como pronto</a>')
        return "Pronto"
    marcar_pronto_link.short_description = "Ação"

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, get_object_or_404
from .models import CardItem

@staff_member_required
def marcar_pronto_view(request, pk):
    item = get_object_or_404(CardItem, pk=pk)
    item.is_ready = True
    item.save()
    return redirect('/admin/restaurants/carditem/')  # ou ajuste conforme o nome do app


    # (o resto igual que mostrei acima)



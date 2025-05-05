import re
from django.db import models
from django.core.exceptions import ValidationError

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.utils.timezone import localdate

User = get_user_model()

from django.utils.crypto import get_random_string
from django.utils.timezone import localdate

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string




class Restaurant(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='restaurante')
    name = models.CharField(_('Name'), max_length=100)
    slug = models.SlugField(_('Slug'), unique=True)
    chave_pix = models.CharField(_('Pix Key'), max_length=100, blank=True)

    address = models.TextField(_('Full Address'))
    street = models.CharField(_('Street'), max_length=255, blank=True)
    number = models.CharField(_('Number'), max_length=20, blank=True)
    neighborhood = models.CharField(_('Neighborhood'), max_length=100, blank=True)
    city = models.CharField(_('City'), max_length=100, blank=True)
    state = models.CharField(_('State'), max_length=2, blank=True)
    zip_code = models.CharField(_('ZIP Code'), max_length=10, blank=True)

    phone = models.CharField(_('Phone'), max_length=20)
    email = models.EmailField(_('Email'))
    logo = models.ImageField(_('Logo'), upload_to='restaurant_logos/', null=True, blank=True)

    is_active = models.BooleanField(_('Active'), default=True)
    emit_nfce = models.BooleanField(_('Emit Fiscal Invoice (NFC-e)?'), default=False)

    cnpj = models.CharField(_('CNPJ'), max_length=14, blank=True)
    state_registration = models.CharField(_('State Registration'), max_length=20, blank=True)
    tax_regime = models.CharField(_('Tax Regime'), max_length=20, choices=[
        ('1', 'Simples Nacional'),
        ('2', 'Simples Excesso Sublimite'),
        ('3', 'Regime Normal'),
    ], default='1', blank=True)

    certificate_file = models.FileField(_('Digital Certificate (.pfx)'), upload_to='certificates/', null=True, blank=True)
    certificate_password = models.CharField(_('Certificate Password'), max_length=100, blank=True)
    csc = models.CharField(_('CSC'), max_length=50, blank=True)
    csc_id = models.CharField(_('CSC ID'), max_length=10, blank=True)

    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    codigo_diario = models.CharField(max_length=20, blank=True)

    def gerar_codigo_diario(self):
        # Gera código no formato RST-AAAA-MM-DD-XYZ
        hoje = localdate()
        base = f"{self.id}-{hoje.isoformat()}"
        aleatorio = get_random_string(length=6)
        self.codigo_diario = f"{base}-{aleatorio}"
        self.save()
        return self.codigo_diario

    class Meta:
        verbose_name = _('Restaurant')
        verbose_name_plural = _('Restaurants')
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()

        # Validação da chave Pix
        if self.chave_pix:
            chave = self.chave_pix.strip()
            padrao_email = r"^[\w\.-]+@[\w\.-]+\.\w+$"
            padrao_telefone = r"^\+55\d{11}$"
            padrao_cpf = r"^\d{11}$"
            padrao_cnpj = r"^\d{14}$"
            padrao_uuid = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

            if not (
                re.match(padrao_email, chave) or
                re.match(padrao_telefone, chave) or
                re.match(padrao_cpf, chave) or
                re.match(padrao_cnpj, chave) or
                re.match(padrao_uuid, chave)
            ):
                raise ValidationError({
                    'chave_pix': _("Invalid Pix key. Must be email, phone (+55...), CPF, CNPJ or UUID.")
                })

        # 🔐 Validação dos dados fiscais apenas se emitir NFC-e
        if self.emit_nfce:
            campos_fiscais = {
                'cnpj': self.cnpj,
                'state': self.state,
                'city': self.city,
                'zip_code': self.zip_code,
                'street': self.street,
                'number': self.number,
                'neighborhood': self.neighborhood,
                'state_registration': self.state_registration,
                'tax_regime': self.tax_regime,
                'certificate_file': self.certificate_file,
                'certificate_password': self.certificate_password,
                'csc': self.csc,
                'csc_id': self.csc_id,
            }

            campos_vazios = [campo for campo, valor in campos_fiscais.items() if not valor]
            if campos_vazios:
                raise ValidationError({
                    campo: _('Required for NFC-e emission.') for campo in campos_vazios
                })

class Table(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='tables', verbose_name='Restaurante')
    number = models.CharField(_('Número'), max_length=10)
    capacity = models.PositiveIntegerField(_('Capacidade'), validators=[MinValueValidator(1)])
    is_occupied = models.BooleanField(_('Ocupada?'), default=False)
    qr_code = models.ImageField(_('QR Code'), upload_to='qr_codes/', null=True, blank=True)

    
    def get_capacity_display(self):
        return f"{self.capacity} pessoas"
    def get_is_occupied_display(self):
        return _('Sim') if self.is_occupied else _('Não')
    def get_qr_code_display(self):
        return self.qr_code.url if self.qr_code else _('Sem QR Code')
   
    class Meta:
        verbose_name = _('Mesa')
        verbose_name_plural = _('Mesas')
        ordering = ['number']
        constraints = [
            models.UniqueConstraint(fields=['restaurant', 'number'], name='unique_table_number_per_restaurant')
        ]

    def __str__(self):
        return f"{self.number} - {self.restaurant.name}"

class Category(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(_('Nome'), max_length=50)
    description = models.TextField(_('Descrição'), blank=True)
    order = models.PositiveIntegerField(_('Ordem'), default=0)

    class Meta:
        verbose_name = _('Categoria')
        verbose_name_plural = _('Categorias')
        ordering = ['order', 'name']

    
    
    def __str__(self):
        return self.name

class MenuItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_items')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='menu_items')
    name = models.CharField(_('Nome'), max_length=100)
    description = models.TextField(_('Descrição'), blank=True)
    price = models.DecimalField(_('Preço'), max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    image = models.ImageField(_('Imagem'), upload_to='menu_items/', null=True, blank=True)
    is_available = models.BooleanField(_('Disponível?'), default=True)
    preparation_time = models.PositiveIntegerField(_('Tempo de preparo (min)'), default=15)
    ingredients = models.TextField(_('Ingredientes'), blank=True)

    class Meta:
        verbose_name = _('Item do Cardápio')
        verbose_name_plural = _('Itens do Cardápio')
        ordering = ['category__order', 'name']

    def __str__(self):
        return f"{self.name} - R$ {self.price:.2f}"

class Customer(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='customers')
    name = models.CharField(_('Nome'), max_length=100)
    phone = models.CharField(_('Telefone'), max_length=20, blank=True)
    email = models.EmailField(_('E-mail'), blank=True)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    notes = models.TextField(_('Observações'), blank=True)

    class Meta:
        verbose_name = _('Cliente')
        verbose_name_plural = _('Clientes')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.phone or 'Sem telefone'}"

class Card(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='cards')
    number = models.PositiveIntegerField(_('Número da Comanda'))
    is_active = models.BooleanField(_('Ativo?'), default=True)



    @property
    def was_paid_today(self):
        today = localdate()
        return self.payments.filter(paid_at__date=today).exists()

    class Meta:
        unique_together = ('id','restaurant', 'number')
        ordering = ['number']
        verbose_name = _('Comanda')
        verbose_name_plural = _('Comandas')

    def __str__(self):
        return f"{self.number} Valor: {sum(item.subtotal() for item in self.card_items.all()):.2f}"
    

    def total(self):
        return sum(item.subtotal() for item in self.card_items.all())

class CardItem(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='card_items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(_('Quantidade'), default=1, validators=[MinValueValidator(1)])
    price = models.DecimalField(
        _('Preço unitário'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        null=True,
        blank=True
    )
    is_ready = models.BooleanField(_('Pronto?'), default=False)

    class Meta:
        verbose_name = _('Item do Cartão')
        verbose_name_plural = _('Itens do Cartão')

    def __str__(self):
        return f"{self.menu_item.name} x{self.quantity}"


    def clean(self):
        """Garante que o preço seja definido antes de salvar"""
        if not self.price and self.menu_item:
            self.price = self.menu_item.price
        super().clean()
    
    def subtotal(self):
        """Calcula o subtotal com tratamento para None"""
        return (self.price or self.menu_item.price) * self.quantity

    subtotal.short_description = _('Subtotal')
        

class Order(models.Model):
    class Status(models.TextChoices):
        PENDING =   'PE', _('Pendente')
        PREPARING = 'PR', _('Em preparo')
        READY =     'RE', _('Pronto')
        DELIVERED = 'DE', _('Entregue')
        CANCELED =  'CA', _('Cancelado')

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, verbose_name='Restaurante', related_name='orders')
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Mesa')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Cliente')
    status = models.CharField(_('Status'), max_length=2, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    notes = models.TextField(_('Observações'), blank=True)

    class Meta:
        verbose_name = _('Pedido')
        verbose_name_plural = _('Pedidos')
        ordering = ['-created_at']

    def __str__(self):
        return f"Pedido #{self.id} - {sum(item.subtotal() for item in self.order_items.all()):.2f}"

    def total(self):
        return sum(item.subtotal() for item in self.order_items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(_('Quantidade'), default=1, validators=[MinValueValidator(1)])
    price = models.DecimalField(
        _('Preço unitário'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        null=True,
        blank=True
    )
    special_requests = models.TextField(_('Pedidos especiais'), blank=True)

    class Meta:
        verbose_name = _('Item do pedido')
        verbose_name_plural = _('Itens do pedido')

    def __str__(self):
        return f"{self.menu_item.name} x{self.quantity}"

    def clean(self):
        """Garante que o preço seja definido antes de salvar"""
        if not self.price and self.menu_item:
            self.price = self.menu_item.price
        super().clean()

    def save(self, *args, **kwargs):
        """Sobrescreve o save para garantir o preço"""
        self.full_clean()
        super().save(*args, **kwargs)

    def subtotal(self):
        """Calcula o subtotal com tratamento para None"""
        return (self.price or self.menu_item.price) * self.quantity

    subtotal.short_description = _('Subtotal')
    
class Stock(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='stocks')
    menu_item = models.OneToOneField(MenuItem, on_delete=models.CASCADE, related_name='stock')
    quantity = models.FloatField(_('Quantidade em estoque'), default=0)

    class Meta:
        verbose_name = _('Estoque')
        verbose_name_plural = _('Estoques')
        ordering = ['menu_item__name']

    def __str__(self):
        return f"{self.menu_item.name} - {self.quantity} unidades"


from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

class CardPayment(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = 'CA', _('Dinheiro')
        CREDIT = 'CR', _('Crédito')
        DEBIT = 'DE', _('Débito')
        PIX = 'PX', _('Pix')
        OTHER = 'OT', _('Outro')

    restaurant = models.ForeignKey('Restaurant', on_delete=models.CASCADE, related_name='card_payments')
    card = models.ForeignKey('Card', on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(_('Valor pago'), max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    payment_method = models.CharField(_('Forma Pagamento'), max_length=2, choices=PaymentMethod.choices)
    paid_amount = models.DecimalField(_('Recebido em Dinheiro'), max_digits=10, decimal_places=2, null=True, blank=True)
    change_amount = models.DecimalField(_('Troco'), max_digits=10, decimal_places=2, null=True, blank=True)
    paid_at = models.DateTimeField(_('Pago em'), auto_now_add=True)
    notes = models.TextField(_('Observações'), blank=True)

    def save(self, *args, **kwargs):
    # Sempre atualiza o valor da venda baseado no total do cartão
        if self.card:
            self.amount = self.card.total()

        if self.payment_method == self.PaymentMethod.CASH:
            if self.paid_amount is not None:
                # Se o operador informou o valor recebido, calcula o troco
                self.change_amount = self.paid_amount - self.amount
            else:
                # Se NÃO informou, assume que recebeu exatamente o valor da venda
                self.paid_amount = self.amount
                self.change_amount = 0
        else:
            # Para outras formas de pagamento, zera esses campos
            self.paid_amount = None
            self.change_amount = None

        super().save(*args, **kwargs)

    def is_paid_today(self):
        return self.payments.filter(paid_at__date=localdate()).exists()

    is_paid_today.boolean = True
    is_paid_today.short_description = "Pago hoje?"
    class Meta:
        verbose_name = _('Recebimento da Comanda')
        verbose_name_plural = _('Recebimento das Comandas')
        ordering = ['-paid_at']

    def __str__(self):
        return f"R$ {self.amount:.2f} no cartão {self.card.number} id:{self.card.id} via {self.get_payment_method_display()}"


from django.db.models.signals import post_save
from django.dispatch import receiver
"""@receiver(post_save, sender=CardPayment)
def atualizar_estoque_ao_receber_pagamento(sender, instance, created, **kwargs):
    if created:  # Só ajusta estoque em novos pagamentos
        card = instance.card
        for item in card.card_items.all():
            menu_item = item.menu_item
            try:
                stock = menu_item.stock  # acessa o Stock pelo OneToOne                
                stock.quantity -= item.quantity
                stock.save()

            except Stock.DoesNotExist:
                # Se não existir controle de estoque ainda para esse item, pode ignorar ou criar
               # Se não existir, cria o estoque já negativo
                Stock.objects.create(
                    restaurant=menu_item.restaurant,
                    menu_item=menu_item,
                    quantity=-item.quantity  # negativo pela quantidade vendida
                )
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=OrderItem)
def baixar_estoque_ao_criar_pedido(sender, instance, created, **kwargs):
    if created:
        menu_item = instance.menu_item
        quantidade = instance.quantity
        try:
            stock = menu_item.stock
            stock.quantity -= quantidade
            stock.save()
        except Stock.DoesNotExist:
            # Se o item não tiver estoque criado ainda, cria com saldo negativo
            Stock.objects.create(
                restaurant=menu_item.restaurant,
                menu_item=menu_item,
                quantity=-quantidade
            )


class StockEntry(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='stock_entries')
    created_at = models.DateTimeField(_('Data de Entrada'), auto_now_add=True)
    supplier = models.CharField(_('Fornecedor'), max_length=255, blank=True)
    notes = models.TextField(_('Observações'), blank=True)

    class Meta:
        verbose_name = _('Nota de Entrada')
        verbose_name_plural = _('Notas de Entrada')
        ordering = ['-created_at']

    def __str__(self):
        return f"Entrada #{self.id} - {self.restaurant.name} - {self.created_at.strftime('%d/%m/%Y')}"


class StockEntryItem(models.Model):
    stock_entry = models.ForeignKey(StockEntry, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(_('Quantidade'), validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = _('Item da Nota de Entrada')
        verbose_name_plural = _('Itens da Nota de Entrada')

    def __str__(self):
        return f"{self.menu_item.name} (+{self.quantity})"

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=StockEntryItem)
def atualizar_estoque_entrada(sender, instance, created, **kwargs):
    if created:
        menu_item = instance.menu_item
        quantidade = instance.quantity

        try:
            stock = menu_item.stock
            stock.quantity += quantidade
            stock.save()
        except Stock.DoesNotExist:
            # Se não existir, cria um estoque inicial positivo
            Stock.objects.create(
                restaurant=menu_item.restaurant,
                menu_item=menu_item,
                quantity=quantidade
            )

@receiver(post_save, sender=CardItem)
def baixar_estoque_ao_adicionar_item_na_comanda(sender, instance, created, **kwargs):
    if created:
        menu_item = instance.menu_item
        quantidade = instance.quantity
        try:
            stock = menu_item.stock
            stock.quantity -= quantidade
            stock.save()
        except Stock.DoesNotExist:
            Stock.objects.create(
                restaurant=menu_item.restaurant,
                menu_item=menu_item,
                quantity=-quantidade
            )




@receiver(post_save, sender=Restaurant)
def gerar_codigo_ao_criar_restaurante(sender, instance, created, **kwargs):
    if created and not instance.codigo_diario:
        hoje = localdate()
        aleatorio = get_random_string(length=6)
        instance.codigo_diario = f"{instance.id}-{hoje.isoformat()}-{aleatorio}"
        instance.save()

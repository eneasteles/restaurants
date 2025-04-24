from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.utils.timezone import localdate

User = get_user_model()

class Restaurant(models.Model):    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='restaurante')
    name = models.CharField(_('Nome'), max_length=100)
    slug = models.SlugField(_('Slug'), unique=True)
    address = models.TextField(_('Endereço'))
    phone = models.CharField(_('Telefone'), max_length=20)
    email = models.EmailField(_('E-mail'))
    logo = models.ImageField(_('Logo'), upload_to='restaurant_logos/', null=True, blank=True)
    is_active = models.BooleanField(_('Ativo'), default=True)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    
    class Meta:
        verbose_name = _('Restaurante')
        verbose_name_plural = _('Restaurantes')
        ordering = ['name']

    def __str__(self):
        return self.name

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
        verbose_name = _('Item do Menu')
        verbose_name_plural = _('Itens do Menu')
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
    number = models.PositiveIntegerField(_('Número do Cartão'))
    is_active = models.BooleanField(_('Ativo?'), default=True)



    @property
    def was_paid_today(self):
        today = localdate()
        return self.payments.filter(paid_at__date=today).exists()

    class Meta:
        unique_together = ('id','restaurant', 'number')
        ordering = ['number']
        verbose_name = _('Cartão')
        verbose_name_plural = _('Cartões')

    def __str__(self):
        return f"Cartão {self.number}/id:{self.id} - {sum(item.subtotal() for item in self.card_items.all()):.2f}"
    

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
    payment_method = models.CharField(_('Forma de pagamento'), max_length=2, choices=PaymentMethod.choices)
    paid_at = models.DateTimeField(_('Pago em'), auto_now_add=True)
    notes = models.TextField(_('Observações'), blank=True)
    def is_paid_today(self):
        return self.payments.filter(paid_at__date=localdate()).exists()

    is_paid_today.boolean = True
    is_paid_today.short_description = "Pago hoje?"
    class Meta:
        verbose_name = _('Recebimento no Cartão')
        verbose_name_plural = _('Recebimentos nos Cartões')
        ordering = ['-paid_at']

    def __str__(self):
        return f"R$ {self.amount:.2f} no cartão {self.card.number} id:{self.card.id} via {self.get_payment_method_display()}"



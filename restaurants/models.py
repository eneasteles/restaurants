from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

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
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='tables')
    number = models.CharField(_('Número'), max_length=10)
    capacity = models.PositiveIntegerField(_('Capacidade'), validators=[MinValueValidator(1)])
    is_occupied = models.BooleanField(_('Ocupada?'), default=False)
    qr_code = models.ImageField(_('QR Code'), upload_to='qr_codes/', null=True, blank=True)

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

class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PE', _('Pendente')
        PREPARING = 'PR', _('Em preparo')
        READY = 'RE', _('Pronto')
        DELIVERED = 'DE', _('Entregue')
        CANCELED = 'CA', _('Cancelado')

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='orders')
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(_('Status'), max_length=2, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    notes = models.TextField(_('Observações'), blank=True)

    class Meta:
        verbose_name = _('Pedido')
        verbose_name_plural = _('Pedidos')
        ordering = ['-created_at']

    def __str__(self):
        return f"Pedido #{self.id} - {self.get_status_display()}"

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
        blank=True  # Permitir temporariamente para migrações existentes
    )
    special_requests = models.TextField(_('Pedidos especiais'), blank=True)

    class Meta:
        verbose_name = _('Item do pedido')
        verbose_name_plural = _('Itens do pedido')

    def __str__(self):
        return f"{self.menu_item.name} x{self.quantity}"

    def clean(self):
        """Garante que o preço seja definido antes de salvar"""
        if not self.price:
            self.price = self.menu_item.price
        super().clean()

    def save(self, *args, **kwargs):
        """Sobrescreve o save para garantir o preço"""
        self.full_clean()  # Executa a validação clean()
        super().save(*args, **kwargs)

    def subtotal(self):
        """Calcula o subtotal com tratamento para None"""
        if self.price is None:
            # Se o preço for None, usa o preço do menu_item
            return self.menu_item.price * self.quantity
        return self.price * self.quantity
    subtotal.short_description = _('Subtotal')


# restaurants/models.py (adicionar isso no final)

class PaymentMethod(models.Model):
    name = models.CharField("Método", max_length=50)  # Ex: "Dinheiro", "Cartão", "PIX"
    is_active = models.BooleanField("Ativo?", default=True)
    needs_change = models.BooleanField("Precisa de troco?", default=False)  # Só True para Dinheiro

    class Meta:
        verbose_name = _('Forma de pagamento')
        verbose_name_plural = _('Formas de pagamento')
        

    def __str__(self):
        return self.name

class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="payments")
    method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
    amount = models.DecimalField("Valor pago", max_digits=10, decimal_places=2)
    change_amount = models.DecimalField("Troco", max_digits=10, decimal_places=2, default=0)
    transaction_code = models.CharField("Código (opcional)", max_length=100, blank=True)
    created_at = models.DateTimeField("Data", auto_now_add=True)

    class Meta:
        verbose_name = _('Pagamento')
        verbose_name_plural = _('Pagamentos')

    def __str__(self):
        return f"Pagamento #{self.id} ({self.method.name})"
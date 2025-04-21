from django.db import models
from restaurants.models import Order
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model

# Create your models here.

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
    order = models.ForeignKey(Order, on_delete=models.PROTECT, verbose_name="Pedido")
    method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, verbose_name="Método de pagamento")
    amount = models.DecimalField("Valor pago", max_digits=10, decimal_places=2)
    change_amount = models.DecimalField("Troco", max_digits=10, decimal_places=2, default=0)
    transaction_code = models.CharField("Código (opcional)", max_length=100, blank=True)
    created_at = models.DateTimeField("Data", auto_now_add=True)

    class Meta:
        verbose_name = _('Pagamento')
        verbose_name_plural = _('Pagamentos')

    def total(self):
        return sum(item.subtotal() for item in self.order_items.all())

    def __str__(self):
        return f"Pagamento #{self.id} ({self.method.name})"
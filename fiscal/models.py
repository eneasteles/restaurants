# fiscal/models.py
# fiscal/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from restaurants.models import CardPayment, Restaurant

class NotaFiscal(models.Model):
    class AmbienteChoices(models.TextChoices):
        PRODUCAO = '1', _('Produção')
        HOMOLOGACAO = '2', _('Homologação')

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='notas_fiscais')
    card_payment = models.OneToOneField(CardPayment, on_delete=models.CASCADE, related_name='nota_fiscal')

    numero = models.PositiveIntegerField(_('Número da Nota'), help_text='Número sequencial da NFC-e')
    serie = models.PositiveIntegerField(_('Série'), default=1)
    chave = models.CharField(_('Chave de Acesso'), max_length=44, unique=True)
    xml = models.TextField(_('XML Assinado'), blank=True)
    danfe_url = models.URLField(_('Link para DANFE'), blank=True)
    qrcode_url = models.URLField(_('Link do QR Code'), blank=True)
    ambiente = models.CharField(_('Ambiente'), max_length=1, choices=AmbienteChoices.choices, default=AmbienteChoices.HOMOLOGACAO)

    emitido_em = models.DateTimeField(_('Emitido em'), auto_now_add=True)

    class Meta:
        verbose_name = _('Nota Fiscal')
        verbose_name_plural = _('Notas Fiscais')
        ordering = ['-emitido_em']

    def __str__(self):
        return f"NFC-e #{self.numero} - {self.restaurant.name}"



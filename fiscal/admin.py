from django.contrib import admin
from fiscal.models import NotaFiscal
from django.utils.html import format_html

from django.http import HttpResponse
import csv
from datetime import datetime

def exportar_notas_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="notas_fiscais_{datetime.now():%Y%m%d}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Número', 'Série', 'CNPJ', 'Chave', 'Valor', 'Emitido em', 'Ambiente'])

    for nota in queryset:
        writer.writerow([
            nota.numero,
            nota.serie,
            nota.restaurant.cnpj,
            nota.chave,
            nota.card_payment.amount,
            nota.emitido_em.strftime('%d/%m/%Y %H:%M'),
            nota.get_ambiente_display()
        ])

    return response

exportar_notas_csv.short_description = "Exportar CSV das notas selecionadas"

@admin.register(NotaFiscal)
class NotaFiscalAdmin(admin.ModelAdmin):
    list_display = (
        'numero', 'restaurant', 'card_payment', 'chave_curta', 
        'ambiente', 'emitido_em', 'link_danfe', 'link_qrcode'
    )
    list_filter = ('ambiente', 'restaurant', 'emitido_em')
    search_fields = ('numero', 'chave', 'restaurant__name', 'card_payment__id')
    ordering = ('-emitido_em',)

    actions = [exportar_notas_csv]  # ⬅️ ESTA LINHA ativa a exportação em massa

    def chave_curta(self, obj):
        return f"{obj.chave[:6]}...{obj.chave[-6:]}"
    chave_curta.short_description = "Chave"

    def link_danfe(self, obj):
        if obj.danfe_url:
            return format_html('<a href="{}" target="_blank">Ver DANFE</a>', obj.danfe_url)
        return "-"
    link_danfe.short_description = "DANFE"

    def link_qrcode(self, obj):
        if obj.qrcode_url:
            return format_html('<a href="{}" target="_blank">QR Code</a>', obj.qrcode_url)
        return "-"
    link_qrcode.short_description = "QR Code"


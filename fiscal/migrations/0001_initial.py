# Generated by Django 5.2 on 2025-05-02 15:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('restaurants', '0023_alter_restaurant_options_restaurant_certificate_file_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotaFiscal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.PositiveIntegerField(help_text='Número sequencial da NFC-e', verbose_name='Número da Nota')),
                ('serie', models.PositiveIntegerField(default=1, verbose_name='Série')),
                ('chave', models.CharField(max_length=44, unique=True, verbose_name='Chave de Acesso')),
                ('xml', models.TextField(blank=True, verbose_name='XML Assinado')),
                ('danfe_url', models.URLField(blank=True, verbose_name='Link para DANFE')),
                ('qrcode_url', models.URLField(blank=True, verbose_name='Link do QR Code')),
                ('ambiente', models.CharField(choices=[('1', 'Produção'), ('2', 'Homologação')], default='2', max_length=1, verbose_name='Ambiente')),
                ('emitido_em', models.DateTimeField(auto_now_add=True, verbose_name='Emitido em')),
                ('card_payment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='nota_fiscal', to='restaurants.cardpayment')),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notas_fiscais', to='restaurants.restaurant')),
            ],
            options={
                'verbose_name': 'Nota Fiscal',
                'verbose_name_plural': 'Notas Fiscais',
                'ordering': ['-emitido_em'],
            },
        ),
    ]

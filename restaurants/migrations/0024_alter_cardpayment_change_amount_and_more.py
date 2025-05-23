# Generated by Django 5.2 on 2025-05-04 21:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurants', '0023_alter_restaurant_options_restaurant_certificate_file_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cardpayment',
            name='change_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Troco'),
        ),
        migrations.AlterField(
            model_name='cardpayment',
            name='paid_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Recebido em Dinheiro'),
        ),
        migrations.AlterField(
            model_name='cardpayment',
            name='payment_method',
            field=models.CharField(choices=[('CA', 'Dinheiro'), ('CR', 'Crédito'), ('DE', 'Débito'), ('PX', 'Pix'), ('OT', 'Outro')], max_length=2, verbose_name='Forma Pagamento'),
        ),
    ]

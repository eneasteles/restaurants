# Generated by Django 5.2 on 2025-05-04 22:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurants', '0024_alter_cardpayment_change_amount_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='restaurant',
            name='codigo_diario',
            field=models.CharField(blank=True, max_length=20),
        ),
    ]

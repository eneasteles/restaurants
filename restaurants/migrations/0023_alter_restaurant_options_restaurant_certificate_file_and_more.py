# Generated by Django 5.2 on 2025-05-02 15:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurants', '0022_alter_card_options_alter_cardpayment_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='restaurant',
            options={'ordering': ['name'], 'verbose_name': 'Restaurant', 'verbose_name_plural': 'Restaurants'},
        ),
        migrations.AddField(
            model_name='restaurant',
            name='certificate_file',
            field=models.FileField(blank=True, null=True, upload_to='certificates/', verbose_name='Digital Certificate (.pfx)'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='certificate_password',
            field=models.CharField(blank=True, max_length=100, verbose_name='Certificate Password'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='city',
            field=models.CharField(blank=True, max_length=100, verbose_name='City'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='cnpj',
            field=models.CharField(blank=True, max_length=14, verbose_name='CNPJ'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='csc',
            field=models.CharField(blank=True, max_length=50, verbose_name='CSC'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='csc_id',
            field=models.CharField(blank=True, max_length=10, verbose_name='CSC ID'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='emit_nfce',
            field=models.BooleanField(default=False, verbose_name='Emit Fiscal Invoice (NFC-e)?'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='neighborhood',
            field=models.CharField(blank=True, max_length=100, verbose_name='Neighborhood'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='number',
            field=models.CharField(blank=True, max_length=20, verbose_name='Number'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='state',
            field=models.CharField(blank=True, max_length=2, verbose_name='State'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='state_registration',
            field=models.CharField(blank=True, max_length=20, verbose_name='State Registration'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='street',
            field=models.CharField(blank=True, max_length=255, verbose_name='Street'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='tax_regime',
            field=models.CharField(blank=True, choices=[('1', 'Simples Nacional'), ('2', 'Simples Excesso Sublimite'), ('3', 'Regime Normal')], default='1', max_length=20, verbose_name='Tax Regime'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='zip_code',
            field=models.CharField(blank=True, max_length=10, verbose_name='ZIP Code'),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='address',
            field=models.TextField(verbose_name='Full Address'),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='chave_pix',
            field=models.CharField(blank=True, max_length=100, verbose_name='Pix Key'),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created At'),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='email',
            field=models.EmailField(max_length=254, verbose_name='Email'),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Active'),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='name',
            field=models.CharField(max_length=100, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='phone',
            field=models.CharField(max_length=20, verbose_name='Phone'),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Updated At'),
        ),
    ]

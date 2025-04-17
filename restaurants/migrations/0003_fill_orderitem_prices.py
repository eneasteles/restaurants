# Generated by Django 5.2 on 2025-04-16 17:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('restaurants', '0002_remove_menuitem_calories_alter_category_restaurant_and_more'),
    ]

    operations = [
    ]

# Generated by Django 5.2 on 2025-04-16 13:45

from django.db import migrations

def fill_prices(apps, schema_editor):
    OrderItem = apps.get_model('restaurants', 'OrderItem')
    for item in OrderItem.objects.filter(price__isnull=True):
        item.price = item.menu_item.price
        item.save()

class Migration(migrations.Migration):

    dependencies = [
        ('restaurants', '0002_remove_menuitem_calories_alter_category_restaurant_and_more'),
    ]

    operations = [
        migrations.RunPython(fill_prices),
    ]
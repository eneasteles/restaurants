from django.contrib import admin
from .models import PaymentMethod, Payment

# Register your models here.

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "needs_change"]

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "method", "amount", "created_at"]
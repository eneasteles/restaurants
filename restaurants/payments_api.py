from ninja import Router
from restaurants.models import Restaurant, Card, CardPayment
from .schemas import PagamentoIn

payment_router = Router()

@payment_router.post("/pagamentos/")
def registrar_pagamento(request, data: PagamentoIn, codigo: str):
    try:
        restaurante = Restaurant.objects.get(codigo_diario=codigo)
        card = Card.objects.get(id=data.card_id, restaurant=restaurante, is_active=True)
    except (Restaurant.DoesNotExist, Card.DoesNotExist):
        return {"error": "Restaurante ou comanda não encontrados"}, 404

    total = sum(item.quantity * item.price for item in card.card_items.all())

    CardPayment.objects.create(
        restaurant=restaurante,
        card=card,
        amount=total,
        payment_method=data.payment_method,
        paid_amount=data.paid_amount,
        change_amount=(data.paid_amount - total) if data.paid_amount else None
    )

    card.is_active = False
    card.save()

    return {"success": True, "total": float(total)}

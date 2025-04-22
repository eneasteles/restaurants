from ninja import Router, Schema
from restaurants.models import Restaurant, Card, CardPayment
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError

router = Router()

class CardPaymentIn(Schema):
    card_id: int
    amount: float
    payment_method: str
    notes: str = ""

@router.post("/card/payment/")
def registrar_pagamento(request, payload: CardPaymentIn):
    restaurante = get_object_or_404(Restaurant, owner=request.user)
    card = get_object_or_404(Card, id=payload.card_id, restaurant=restaurante)

    total = sum(item.subtotal() for item in card.card_items.all())

    if payload.amount < total:
        raise HttpError(400, f"O valor pago R$ {payload.amount:.2f} é inferior ao total R$ {total:.2f}.")

    CardPayment.objects.create(
        restaurant=restaurante,
        card=card,
        amount=payload.amount,
        payment_method=payload.payment_method,
        notes=payload.notes
    )

    return {"message": f"Pagamento de R$ {payload.amount:.2f} registrado com sucesso para o cartão {card.number}."}

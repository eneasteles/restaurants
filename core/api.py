from ninja import NinjaAPI, Router, Schema
from restaurants.models import Restaurant, Card, CardPayment
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError
from core.api_views import router as core_router
 # supondo que seus endpoints estejam aqui
from ninja import NinjaAPI
from restaurants.api import router as restaurants_router
from cashier.api import router as cashier_router
api = NinjaAPI()

api.add_router("/restaurants/", restaurants_router)
api.add_router("/cashier/", cashier_router)

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

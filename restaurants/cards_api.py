from ninja import Router, Schema
from typing import List
from restaurants.models import Restaurant, Card, MenuItem, CardItem
from django.utils.timezone import now
from django.shortcuts import get_object_or_404

card_router = Router(tags=["comandas"])

# Schemas de entrada
class NovaComandaSchema(Schema):
    number: int

class AdicionarItemSchema(Schema):
    card_id: int
    menu_item_id: int
    quantity: int

# GET /api/cards/?codigo=...
@card_router.get("/cards/")
def listar_comandas(request):
    codigo = request.GET.get("codigo")
    if not codigo:
        return {"error": "Código ausente"}, 400

    try:
        restaurante = Restaurant.objects.get(codigo_diario=codigo)
    except Restaurant.DoesNotExist:
        return {"error": "Código inválido 3"}, 404


    cards = Card.objects.filter(restaurant=restaurante, is_active=True).order_by("number")


    return {
        "cards": [
            {
                "id": card.id,
                "number": card.number,
                "created_at": card.created_at,
                "itens": [
                    {
                        "id": item.id,
                        "menu_item_name": item.menu_item.name,
                        "quantity": item.quantity
                    }
                    for item in card.items.select_related("menu_item").all()
                ]
            }
            for card in cards
        ]
    }

# POST /api/cards/abrir/?codigo=...
@card_router.post("/cards/abrir/")
def abrir_comanda(request, data: NovaComandaSchema):
    codigo = request.GET.get("codigo")
    if not codigo:
        return {"error": "Código ausente"}, 400

    try:
        restaurante = Restaurant.objects.get(codigo_diario=codigo)
    except Restaurant.DoesNotExist:
        return {"error": "Código inválido aqui 1"}, 404

    card = Card.objects.create(restaurant=restaurante, number=data.number, is_active=True )
    return {"success": True, "card_id": card.id}


# POST /api/cards/adicionar-item/?codigo=...
@card_router.post("/cards/adicionar-item/")
def adicionar_item(request, data: AdicionarItemSchema):
    codigo = request.GET.get("codigo")
    if not codigo:
        return {"error": "Código ausente"}, 400

    try:
        restaurante = Restaurant.objects.get(codigo_diario=codigo)
    except Restaurant.DoesNotExist:
        return {"error": "Código inválido 2"}, 404

    card = get_object_or_404(Card, id=data.card_id, restaurant=restaurante)
    menu_item = get_object_or_404(MenuItem, id=data.menu_item_id, restaurant=restaurante)

    CardItem.objects.create(card=card, menu_item=menu_item, quantity=data.quantity)
    return {"success": True}

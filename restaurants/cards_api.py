# restaurants/cards_api.py
from ninja import Router
from typing import List
from restaurants.models import Restaurant, Card, CardItem, MenuItem
from .schemas import NovaComandaIn, AdicionarItemIn, ComandaOut, ItemDaComandaOut

card_router = Router()

@card_router.get("/cards/", response=List[ComandaOut])
def listar_comandas(request, codigo: str):
    try:
        restaurante = Restaurant.objects.get(codigo_diario=codigo)
    except Restaurant.DoesNotExist:
        return []

    cards = Card.objects.filter(restaurant=restaurante, is_active=True)

    resultado = []
    for card in cards:
        itens = [
            ItemDaComandaOut(
                menu_item_name=item.menu_item.name,
                quantity=item.quantity
            )
            for item in card.card_items.select_related("menu_item")
        ]
        resultado.append(
            ComandaOut(id=card.id, number=card.number, itens=itens)
        )

    return resultado

@card_router.post("/cards/abrir/")
def abrir_comanda(request, data: NovaComandaIn, codigo: str):
    try:
        restaurante = Restaurant.objects.get(codigo_diario=codigo)
    except Restaurant.DoesNotExist:
        return {"error": "Código inválido"}, 404

    card = Card.objects.create(
        restaurant=restaurante,
        number=data.number,
        is_active=True
    )
    return {"success": True, "card_id": card.id}

@card_router.post("/cards/adicionar-item/")
def adicionar_item(request, data: AdicionarItemIn, codigo: str):
    try:
        restaurante = Restaurant.objects.get(codigo_diario=codigo)
        card = Card.objects.get(id=data.card_id, restaurant=restaurante)
        menu_item = MenuItem.objects.get(id=data.menu_item_id, restaurant=restaurante)
    except (Restaurant.DoesNotExist, Card.DoesNotExist, MenuItem.DoesNotExist):
        return {"error": "Dados inválidos"}, 404

    CardItem.objects.create(
        card=card,
        menu_item=menu_item,
        quantity=data.quantity,
        price=menu_item.price
    )
    return {"success": True}

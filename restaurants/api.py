from ninja import Router
from .models import Table, Category, MenuItem,CardItem
from typing import List
from ninja import Schema
from pydantic import BaseModel
from django.db.models import Prefetch
from pydantic import BaseModel



from django.shortcuts import get_object_or_404
from restaurants.models import Restaurant
from restaurants.cards_api import card_router

def restaurante_por_codigo(request):
    codigo = request.GET.get("codigo")

    if not codigo:
        return None
    return get_object_or_404(Restaurant, codigo_diario=codigo)


router = Router()
class MarkReadySchema(BaseModel):
    id: int







kitchen_router = Router()
# Schemas de exemplo
class MesaOut(Schema):
    id: int
    number: str
    capacity: int

@router.get("/mesas/", response=List[MesaOut])
def listar_mesas(request):
    restaurante = request.user.restaurante_set.first()
    return Table.objects.filter(restaurant=restaurante)




@kitchen_router.get("/kitchen/")
def listar_itens_pendentes(request):
    codigo = request.GET.get("codigo")
    if not codigo:
        return {"error": "Código ausente"}, 400

    try:
        restaurante = Restaurant.objects.get(codigo_diario=codigo)
    except Restaurant.DoesNotExist:
        return {"error": "Código inválido"}, 404

    itens = CardItem.objects.filter(
        is_ready=False,
        card__restaurant=restaurante
    ).select_related("menu_item", "card")

    return {
        "items": [
            {
                "id": item.id,
                "card_number": item.card.number,
                "menu_item_name": item.menu_item.name,
                "quantity": item.quantity
            }
            for item in itens
        ]
    }

@kitchen_router.post("/kitchen/mark-ready/")
def marcar_item_pronto(request, data: MarkReadySchema):
    codigo = request.GET.get("codigo")

    if not codigo:
        return {"error": "Código ausente"}, 400

    try:
        restaurante = Restaurant.objects.get(codigo_diario=codigo)
    except Restaurant.DoesNotExist:
        return {"error": "Código inválido"}, 404

    try:
        item = CardItem.objects.get(pk=data.id, card__restaurant=restaurante)
        item.is_ready = True
        item.save()
        return {"success": True}
    except CardItem.DoesNotExist:
        return {"success": False, "error": "Item não encontrado"}





# restaurants/api.py







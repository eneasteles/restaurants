from ninja import Router
from restaurants.models import Restaurant, MenuItem

menu_router = Router(tags=["cardápio"])

@menu_router.get("/menu-items/")
def listar_menu_items(request):
    codigo = request.GET.get("codigo")
    if not codigo:
        return {"error": "Código ausente"}, 400

    try:
        restaurante = Restaurant.objects.get(codigo_diario=codigo)
    except Restaurant.DoesNotExist:
        return {"error": "Código inválido"}, 404

    items = MenuItem.objects.filter(restaurant=restaurante).order_by("name")

    return {
        "items": [
            {"id": item.id, "name": item.name}
            for item in items
        ]
    }


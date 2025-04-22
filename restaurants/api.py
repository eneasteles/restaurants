from ninja import Router
from .models import Table, Category, MenuItem
from typing import List
from ninja import Schema

router = Router()

# Schemas de exemplo
class MesaOut(Schema):
    id: int
    number: str
    capacity: int

@router.get("/mesas/", response=List[MesaOut])
def listar_mesas(request):
    restaurante = request.user.restaurante_set.first()
    return Table.objects.filter(restaurant=restaurante)

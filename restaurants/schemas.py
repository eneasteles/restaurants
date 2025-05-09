# restaurants/schemas.py
from ninja import Schema
from typing import List
from decimal import Decimal
from typing import Optional

class PagamentoIn(Schema):
    card_id: int
    payment_method: str  # ex: CA, CR, DE, PX
    paid_amount: Optional[float] = None

class MenuItemOut(Schema):
    id: int
    name: str
    price: Decimal

class NovaComandaIn(Schema):
    number: int

class AdicionarItemIn(Schema):
    card_id: int
    menu_item_id: int
    quantity: int

class ItemDaComandaOut(Schema):
    menu_item_name: str
    quantity: int

class ComandaOut(Schema):
    id: int
    number: int
    itens: List[ItemDaComandaOut]

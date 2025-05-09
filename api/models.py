from pydantic import BaseModel, Field, validator
from decimal import Decimal
from typing import List, Optional
from django.core.exceptions import ObjectDoesNotExist
from restaurants.models import MenuItem, Card, CardItem, Restaurant

class MenuItemSchema(BaseModel):
    id: int
    name: str
    price: Decimal
    is_available: bool

    class Config:
        orm_mode = True

class CardItemSchema(BaseModel):
    id: int
    menu_item: MenuItemSchema
    quantity: int
    price: Decimal
    subtotal: Decimal

    class Config:
        orm_mode = True

class CardSchema(BaseModel):
    id: int
    number: int
    is_active: bool
    card_items: List[CardItemSchema]
    total: Decimal

    class Config:
        orm_mode = True

class CardItemCreateSchema(BaseModel):
    menu_item_id: int
    quantity: int = Field(..., gt=0)

    @validator('menu_item_id')
    def validate_menu_item(cls, value, values, **kwargs):
        try:
            restaurant = values.get('context', {}).get('restaurant')
            if not restaurant:
                raise ValueError("Contexto do restaurante não fornecido.")
            menu_item = MenuItem.objects.get(id=value, is_available=True, restaurant=restaurant)
            # Validar estoque
            try:
                stock = menu_item.stock
                if stock.quantity < values.get('quantity', 0):
                    raise ValueError(f"Estoque insuficiente para {menu_item.name}. Disponível: {stock.quantity}.")
            except MenuItem.stock.RelatedObjectDoesNotExist:
                raise ValueError(f"Estoque não configurado para {menu_item.name}.")
            return value
        except ObjectDoesNotExist:
            raise ValueError("Item do cardápio inválido ou não disponível.")

class CardPaymentCreateSchema(BaseModel):
    card_id: int
    payment_method: str
    paid_amount: Optional[Decimal] = None
    notes: Optional[str] = ""

    @validator('payment_method')
    def validate_payment_method(cls, value):
        valid_methods = ['CA', 'CR', 'DE', 'PX', 'OT']
        if value not in valid_methods:
            raise ValueError("Método de pagamento inválido.")
        return value

    @validator('card_id')
    def validate_card(cls, value, values, **kwargs):
        try:
            restaurant = values.get('context', {}).get('restaurant')
            if not restaurant:
                raise ValueError("Contexto do restaurante não fornecido.")
            card = Card.objects.get(id=value, is_active=True, restaurant=restaurant)
            return value
        except ObjectDoesNotExist:
            raise ValueError("Comanda inválida ou não ativa.")

    @validator('paid_amount')
    def validate_paid_amount(cls, value, values):
        if 'payment_method' in values and values['payment_method'] == 'CA' and value is not None:
            try:
                restaurant = values.get('context', {}).get('restaurant')
                if not restaurant:
                    raise ValueError("Contexto do restaurante não fornecido.")
                card = Card.objects.get(id=values['card_id'], restaurant=restaurant)
                total = card.total()
                if value < total:
                    raise ValueError("Valor recebido insuficiente.")
            except ObjectDoesNotExist:
                pass
        return value

    class Config:
        arbitrary_types_allowed = True

class UserProfileSchema(BaseModel):
    restaurant_id: int
    role: str
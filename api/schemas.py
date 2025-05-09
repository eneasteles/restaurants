from pydantic import BaseModel, Field
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
        from_attributes = True

class CardItemSchema(BaseModel):
    id: int
    menu_item: MenuItemSchema
    quantity: int
    price: Decimal
    subtotal: Decimal

    class Config:
        from_attributes = True

class CardSchema(BaseModel):
    id: int
    number: int
    is_active: bool
    card_items: List[CardItemSchema]
    total: Decimal

    @classmethod
    def from_orm(cls, obj):
        # Converter RelatedManager para lista de CardItemSchema
        card_items = []
        for item in obj.card_items.all():
            card_items.append(CardItemSchema(
                id=item.id,
                menu_item=MenuItemSchema.from_orm(item.menu_item),
                quantity=item.quantity,
                price=item.price,
                subtotal=item.subtotal()
            ))
        
        # Calcular total manualmente
        total = sum(item.subtotal() for item in obj.card_items.all())
        
        return cls(
            id=obj.id,
            number=obj.number,
            is_active=obj.is_active,
            card_items=card_items,
            total=total
        )

    class Config:
        from_attributes = True
class CardItemCreateSchema(BaseModel):
    menu_item_id: int
    quantity: int

class CardPaymentCreateSchema(BaseModel):
    card_id: int
    payment_method: str
    paid_amount: Optional[Decimal]
    notes: Optional[str]

class UserProfileSchema(BaseModel):
    restaurant_id: int
    role: str

    class Config:
        from_attributes = True
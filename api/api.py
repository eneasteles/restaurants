from ninja import NinjaAPI, Router
from ninja.security import HttpBearer
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from restaurants.models import Card, MenuItem, CardItem, CardPayment, Restaurant, RestaurantUser
from .schemas import CardSchema, MenuItemSchema, CardItemCreateSchema, CardPaymentCreateSchema, UserProfileSchema
from ninja.errors import ValidationError
from decimal import Decimal
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from django.utils import timezone
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        print(f"Validando token para {request.path}: {token[:20]}...")
        try:
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            print(f"Usuário autenticado: {user.username}, ID: {user.id}")
            request.user = user
            return user
        except (InvalidToken, AuthenticationFailed) as e:
            print(f"Erro na autenticação JWT para {request.path}: {str(e)}")
            return None

api = NinjaAPI(auth=JWTAuth())
menu_router = Router(auth=JWTAuth())  # Explicitamente aplicar JWTAuth

def get_user_restaurant_and_role(user):
    try:
        restaurant_user = RestaurantUser.objects.get(user=user)
        return restaurant_user.restaurant, restaurant_user.role
    except RestaurantUser.DoesNotExist:
        raise Exception("Usuário não associado a um restaurante")

@api.get("/user-profile", response=UserProfileSchema)
def get_user_profile(request):
    print(f"Usuário na requisição: {request.user}, Autenticado: {request.user.is_authenticated}")
    user = request.user
    if not user.is_authenticated:
        print("Autenticação falhou: usuário não autenticado")
        return api.create_response(request, {"error": "Autenticação necessária"}, status=401)
    try:
        restaurant, role = get_user_restaurant_and_role(user)
        print(f"Restaurante: {restaurant}, Papel: {role}")
        return {"restaurant_id": restaurant.id, "role": role}
    except Exception as e:
        print(f"Erro ao obter restaurante/papel: {str(e)}")
        return api.create_response(request, {"error": str(e)}, status=400)

@api.get("/cards", response=list[CardSchema])
def list_cards(request):
    user = request.user
    if not user.is_authenticated:
        return api.create_response(request, {"error": "Autenticação necessária"}, status=401)
    
    restaurant, _ = get_user_restaurant_and_role(user)
    cards = Card.objects.filter(restaurant=restaurant, is_active=True)
    
    # Forçar a serialização manual
    return [CardSchema.from_orm(card) for card in cards]

@menu_router.get("/menu-items", response=list[MenuItemSchema])
def list_menu_items(request):
    print(f"Requisição para /api/menu-items, usuário: {request.user}, autenticado: {request.user.is_authenticated}")
    user = request.user
    if not user.is_authenticated:
        print("Autenticação falhou: usuário não autenticado")
        return api.create_response(request, {"error": "Autenticação necessária"}, status=401)
    restaurant, _ = get_user_restaurant_and_role(user)
    menu_items = MenuItem.objects.filter(restaurant=restaurant, is_available=True)
    print(f"Itens encontrados: {list(menu_items)}")
    return menu_items

@api.post("/cards/{card_id}/items")
def add_card_item(request, card_id: int, payload: CardItemCreateSchema):
    user = request.user
    if not user.is_authenticated:
        return api.create_response(request, {"error": "Autenticação necessária"}, status=401)
    restaurant, _ = get_user_restaurant_and_role(user)
    card = get_object_or_404(Card, id=card_id, restaurant=restaurant)
    menu_item = get_object_or_404(MenuItem, id=payload.menu_item_id, restaurant=restaurant)
    try:
        card_item = CardItem.objects.create(
            card=card,
            menu_item=menu_item,
            quantity=payload.quantity,
            price=menu_item.price
        )
        return {"id": card_item.id, "menu_item_id": menu_item.id, "quantity": card_item.quantity}
    except Exception as e:
        return api.create_response(request, {"error": str(e)}, status=400)

@api.delete("/cards/{card_id}/items/{item_id}")
def delete_card_item(request, card_id: int, item_id: int):
    user = request.user
    if not user.is_authenticated:
        return api.create_response(request, {"error": "Autenticação necessária"}, status=401)
    restaurant, _ = get_user_restaurant_and_role(user)
    card = get_object_or_404(Card, id=card_id, restaurant=restaurant)
    card_item = get_object_or_404(CardItem, id=item_id, card=card)
    card_item.delete()
    return {"success": True}

@api.post("/card-payments", response=CardPaymentCreateSchema)
def create_payment(request, payload: CardPaymentCreateSchema):
    user = request.user
    if not user.is_authenticated:
        return api.create_response(request, {"error": "Autenticação necessária"}, status=401)
    restaurant, _ = get_user_restaurant_and_role(user)
    card = get_object_or_404(Card, id=payload.card_id, restaurant=restaurant)
    try:
        payment = CardPayment.objects.create(
            card=card,
            payment_method=payload.payment_method,
            paid_amount=payload.paid_amount,
            notes=payload.notes
        )
        return {
            "card_id": payment.card.id,
            "payment_method": payment.payment_method,
            "paid_amount": payment.paid_amount,
            "notes": payment.notes
        }
    except Exception as e:
        return api.create_response(request, {"error": str(e)}, status=400)

@api.get("/card-payments/{card_id}/receipt")
def get_receipt(request, card_id: int):
    user = request.user
    if not user.is_authenticated:
        return api.create_response(request, {"error": "Autenticação necessária"}, status=401)
    restaurant, _ = get_user_restaurant_and_role(user)
    card = get_object_or_404(Card, id=card_id, restaurant=restaurant)
    payment = get_object_or_404(CardPayment, card=card)
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, f"Recibo - Comanda {card.number}")
    p.drawString(100, 730, f"Restaurante: {restaurant.name}")
    p.drawString(100, 710, f"Data: {timezone.now().strftime('%d/%m/%Y %H:%M')}")
    p.drawString(100, 690, f"Método de Pagamento: {payment.payment_method}")
    p.drawString(100, 670, f"Valor Pago: R$ {payment.paid_amount}")
    y = 650
    for item in card.card_items.all():
        p.drawString(100, y, f"{item.quantity}x {item.menu_item.name} - R$ {item.subtotal()}")
        y -= 20
    p.drawString(100, y - 20, f"Total: R$ {card.total()}")
    p.showPage()
    p.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

api.add_router("/", menu_router)

@api.get("/cards/{card_id}", response=CardSchema)
def get_card_details(request, card_id: int):
    user = request.user
    if not user.is_authenticated:
        return api.create_response(request, {"error": "Autenticação necessária"}, status=401)
    
    restaurant, _ = get_user_restaurant_and_role(user)
    card = get_object_or_404(Card, id=card_id, restaurant=restaurant)
    return CardSchema.from_orm(card)
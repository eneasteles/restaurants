import flet as ft
from decimal import Decimal, InvalidOperation
import requests
from requests.exceptions import RequestException
import base64
import threading
import qrcode
from io import BytesIO
from PIL import Image

# Global variables (minimized)
API_BASE_URL = "http://103.199.187.28:8001/api/"

# Global variables (minimized)
API_BASE_URL = "http://localhost:8000/api/"
#API_BASE_URL = "http://103.199.187.28:8001/api/"

HEADERS = {}
RESTAURANT_ID = None
comandas = []
page = None

def main(page_param: ft.Page):
    global page
    page = page_param
    page.title = "Caixa do Restaurante - Pagamentos"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 5  # Reduced padding for mobile
    page.window_width = 900
    page.window_height = 700
    page.bgcolor = ft.Colors.GREY_100
    page.viewport_scale = True
    page.web_head = """
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    """
    page.add(
        ft.SafeArea(
            content=ft.Column([]),
            minimum_padding=5,
        )
    )
    show_login_screen()

def login(username, password):
    print(f"Tentando login com usuário: {username}")
    try:
        response = requests.post(f"{API_BASE_URL}token/", data={"username": username, "password": password}, timeout=5)
        print(f"Resposta do /api/token/: {response.status_code}, {response.text}")
        response.raise_for_status()
        data = response.json()
        access_token = data.get("access")
        refresh_token = data.get("refresh")
        if not access_token or not refresh_token:
            raise RequestException("Resposta da API não contém access_token ou refresh_token")
        page.client_storage.clear()
        page.client_storage.set("access_token", access_token)
        page.client_storage.set("refresh_token", refresh_token)
        headers = {"Authorization": f"Bearer {access_token}"}
        user_response = requests.get(f"{API_BASE_URL}user-profile", headers=headers, timeout=5)
        print(f"Resposta do /api/user-profile: {user_response.status_code}, {user_response.text}")
        user_response.raise_for_status()
        profile = user_response.json()
        if "restaurant_id" not in profile:
            raise RequestException("Resposta do /user-profile não contém restaurant_id")
        restaurant_id = profile["restaurant_id"]
        page.client_storage.set("restaurant_id", restaurant_id)
        print(f"Login bem-sucedido: restaurant_id={restaurant_id}, role={profile.get('role', 'N/A')}")
        return headers, restaurant_id, None
    except RequestException as e:
        print(f"Erro no login: {str(e)}")
        return None, None, str(e)
    except Exception as e:
        print(f"Erro inesperado no login: {str(e)}")
        return None, None, f"Erro inesperado: {str(e)}"

def fetch_menu_items():
    restaurant_id = page.client_storage.get("restaurant_id")
    print(f"Buscando itens do cardápio... restaurant_id={restaurant_id}")
    page.client_storage.remove("menu_items")
    try:
        response = requests.get(f"{API_BASE_URL}menu-items", headers=HEADERS)
        print(f"Resposta do /api/menu-items: {response.status_code}, {response.text}")
        response.raise_for_status()
        menu_items = response.json()
        for item in menu_items:
            if item.get("restaurant_id") != restaurant_id:
                print(f"Erro: Item {item['name']} tem restaurant_id={item['restaurant_id']}, esperado={restaurant_id}")
                raise RequestException("Itens de outro restaurante detectados")
        page.client_storage.set("menu_items", menu_items)
        return menu_items
    except RequestException as e:
        print(f"Erro ao buscar itens: {str(e)}")
        page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao buscar itens do cardápio: {str(e)}."))
        page.snack_bar.open = True
        page.update()
        return []

def fetch_comandas():
    restaurant_id = page.client_storage.get("restaurant_id")
    print(f"Buscando comandas... restaurant_id={restaurant_id}")
    page.client_storage.remove("comandas")
    try:
        response = requests.get(f"{API_BASE_URL}cards", headers=HEADERS)
        print(f"Resposta do /api/cards: {response.status_code}, {response.text}")
        if response.status_code == 401:
            print("Token expirado, tentando renovar...")
            refresh_token = page.client_storage.get("refresh_token")
            if not refresh_token:
                raise RequestException("Nenhum refresh_token disponível. Faça login novamente.")
            response = requests.post(f"{API_BASE_URL}token/refresh/", json={"refresh": refresh_token})
            print(f"Resposta do /api/token/refresh/: {response.status_code}, {response.text}")
            if response.status_code == 200:
                data = response.json()
                new_access_token = data.get("access")
                if not new_access_token:
                    raise RequestException("Resposta da renovação não contém access_token")
                HEADERS["Authorization"] = f"Bearer {new_access_token}"
                page.client_storage.set("access_token", new_access_token)
                response = requests.get(f"{API_BASE_URL}cards", headers=HEADERS)
            else:
                raise RequestException(f"Erro ao renovar token: {response.status_code} {response.text}")
        response.raise_for_status()
        comandas[:] = response.json()
        print(f"Comandas recebidas: {comandas}")
        for comanda in comandas:
            if comanda.get("restaurant_id") != restaurant_id:
                print(f"Erro: Comanda {comanda['number']} tem restaurant_id={comanda['restaurant_id']}, esperado={restaurant_id}")
                raise RequestException("Comandas de outro restaurante detectadas")
        page.client_storage.set("comandas", comandas)
        return comandas
    except RequestException as e:
        print(f"Erro ao buscar comandas: {str(e)}")
        page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao buscar comandas: {str(e)}."))
        page.snack_bar.open = True
        page.update()
        if "Faça login novamente" in str(e):
            show_login_screen(error_message="Sessão expirada. Faça login novamente.")
        return []

def create_comanda():
    restaurant_id = page.client_storage.get("restaurant_id")
    print(f"Criando nova comanda... restaurant_id={restaurant_id}")
    try:
        response = requests.post(f"{API_BASE_URL}cards", headers=HEADERS)
        print(f"Resposta do /api/cards (POST): {response.status_code}, {response.text}")
        response.raise_for_status()
        new_comanda = response.json()
        if new_comanda.get("restaurant_id") != restaurant_id:
            print(f"Erro: Nova comanda {new_comanda['number']} tem restaurant_id={new_comanda['restaurant_id']}, esperado={restaurant_id}")
            raise RequestException("Comanda criada com restaurante incorreto")
        
        original_number = int(new_comanda.get("number", 0))
        new_number = original_number + 1000
        patch_data = {"number": new_number}
        patch_response = requests.patch(
            f"{API_BASE_URL}cards/{new_comanda['id']}",
            headers=HEADERS,
            json=patch_data
        )
        print(f"Resposta do /api/cards/{new_comanda['id']} (PATCH): {patch_response.status_code}, {patch_response.text}")
        patch_response.raise_for_status()
        
        new_comanda["number"] = new_number
        page.client_storage.remove("comandas")
        comandas.append(new_comanda)
        
        if hasattr(page, 'comanda_dropdown') and page.comanda_dropdown is not None:
            page.comanda_dropdown.options = [ft.dropdown.Option(f"Comanda {c['number']} (ID: {c['id']})") for c in comandas if c["is_active"]]
            page.comanda_dropdown.value = f"Comanda {new_comanda['number']} (ID: {new_comanda['id']})"
            print(f"Dropdown atualizado com nova comanda: {new_comanda['number']}")
        else:
            print("Aviso: page.comanda_dropdown não definido, dropdown não atualizado")
        
        atualizar_tabela_comanda()
        print("Tabela de comanda atualizada")
        
        page.snack_bar = ft.SnackBar(ft.Text(f"Comanda {new_comanda['number']} criada com sucesso!"))
        page.snack_bar.open = True
        page.update()
        return new_comanda
    except RequestException as e:
        print(f"Erro ao criar comanda: {str(e)}")
        page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao criar comanda: {str(e)}."))
        page.snack_bar.open = True
        page.update()
        return None

def fetch_restaurant_pix_key():
    restaurant_id = page.client_storage.get("restaurant_id")
    print(f"Buscando chave Pix do restaurante... restaurant_id={restaurant_id}")
    try:
        response = requests.get(f"{API_BASE_URL}restaurants/{restaurant_id}", headers=HEADERS)
        print(f"Resposta do /api/restaurants/{restaurant_id}: {response.status_code}, {response.text}")
        response.raise_for_status()
        restaurant_data = response.json()
        pix_key = restaurant_data.get("chave_pix")
        if not pix_key:
            raise RequestException("Chave Pix não configurada para o restaurante")
        return pix_key
    except RequestException as e:
        print(f"Erro ao buscar chave Pix: {str(e)}")
        page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao buscar chave Pix: {str(e)}"))
        page.snack_bar.open = True
        page.update()
        return None

def generate_pix_qr_code(pix_key, amount, restaurant_name):
    print(f"Gerando QR code para Pix: chave={pix_key}, valor={amount}, restaurante={restaurant_name}")
    pix_payload = f"00020126360014BR.GOV.BCB.PIX0114{pix_key}5204000053039865406{amount:.2f}5802BR5913{restaurant_name[:25]}6008BRASILIA62070503***6304"
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(pix_payload)
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    qr_image.save(buffer, format="PNG")
    return buffer.getvalue()

def show_login_screen(error_message=None):
    print("Exibindo tela de login")
    username_field = ft.TextField(
        label="Usuário",
        prefix_icon=ft.Icons.PERSON,
        width=min(page.width * 0.85, 300),
        border_radius=10,
        border_color=ft.Colors.GREY_400,
        text_size=14 if page.width < 600 else 16,
    )
    password_field = ft.TextField(
        label="Senha",
        prefix_icon=ft.Icons.LOCK,
        password=True,
        can_reveal_password=True,
        width=min(page.width * 0.85, 300),
        border_radius=10,
        border_color=ft.Colors.GREY_400,
        text_size=14 if page.width < 600 else 16,
    )
    error_message_text = ft.Text(error_message, color=ft.Colors.RED_600, visible=bool(error_message), size=12 if page.width < 600 else 14)
    loading = ft.ProgressRing(visible=False, width=20 if page.width < 600 else 24, height=20 if page.width < 600 else 24)

    def handle_login(e):
        print("Botão Entrar clicado")
        error_message_text.visible = False
        loading.visible = True
        page.update()

        if not username_field.value or not password_field.value:
            error_message_text.value = "Por favor, preencha usuário e senha."
            error_message_text.visible = True
            loading.visible = False
            page.update()
            return

        headers, restaurant_id, error = login(username_field.value, password_field.value)
        loading.visible = False

        if headers and restaurant_id is not None:
            HEADERS.clear()
            HEADERS.update(headers)
            print(f"handle_login: Definindo restaurant_id={restaurant_id} em client_storage")
            page.client_storage.set("restaurant_id", restaurant_id)
            show_main_interface()
        else:
            error_message_text.value = f"Erro de autenticação: {error or 'Falha ao obter ID do restaurante. Verifique suas credenciais ou conexão com o servidor.'}"
            error_message_text.visible = True
        page.update()

    login_container = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "Sistema de Caixa",
                    size=24 if page.width < 600 else 28,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_900,
                ),
                ft.Text(
                    "Faça login para continuar",
                    size=14 if page.width < 600 else 16,
                    color=ft.Colors.GREY_600,
                ),
                ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                username_field,
                password_field,
                error_message_text,
                ft.Row(
                    [
                        ft.ElevatedButton(
                            content=ft.Row(
                                [
                                    ft.Text("Entrar", size=14 if page.width < 600 else 16, weight=ft.FontWeight.BOLD),
                                    loading,
                                ],
                                spacing=5,
                            ),
                            bgcolor=ft.Colors.GREEN_400,
                            color=ft.Colors.WHITE,
                            width=min(page.width * 0.85, 300),
                            height=40 if page.width < 600 else 50,
                            on_click=handle_login,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        ),
        width=min(page.width * 0.9, 400),
        padding=20,
        bgcolor=ft.Colors.WHITE,
        border_radius=15,
        shadow=ft.BoxShadow(
            blur_radius=10,
            spread_radius=2,
            color=ft.Colors.GREY_300,
        ),
        alignment=ft.alignment.center,
    )

    page.controls.clear()
    page.add(
        ft.Container(
            content=login_container,
            alignment=ft.alignment.center,
            expand=True,
        )
    )
    page.update()

def add_card_item(card_id, menu_item_id, quantity):
    print(f"Adicionando item: card_id={card_id}, menu_item_id={menu_item_id}, quantity={quantity}")
    try:
        data = {"menu_item_id": menu_item_id, "quantity": float(quantity)}
        print(f"Payload enviado: {data}")
        response = requests.post(f"{API_BASE_URL}cards/{card_id}/items", json=data, headers=HEADERS)
        print(f"Resposta do /api/cards/{card_id}/items: {response.status_code}, {response.text}")
        response.raise_for_status()
        result = response.json()
        print(f"Resposta processada: {result}")
        page.client_storage.remove("comandas")
        return result
    except RequestException as e:
        print(f"Erro ao adicionar item: {str(e)}")
        page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao adicionar item: {str(e)}"))
        page.snack_bar.open = True
        page.update()
        return None

def delete_card_item(card_id, item_id):
    print(f"Removendo item: card_id={card_id}, item_id={item_id}")
    try:
        response = requests.delete(f"{API_BASE_URL}cards/{card_id}/items/{item_id}", headers=HEADERS)
        print(f"Resposta do /api/cards/{card_id}/items/{item_id}: {response.status_code}, {response.text}")
        response.raise_for_status()
        page.client_storage.remove("comandas")
        return True
    except RequestException as e:
        print(f"Erro ao remover item: {str(e)}")
        page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao remover item: {str(e)}"))
        page.snack_bar.open = True
        page.update()
        return False

def create_payment(card_id, payment_method, paid_amount=None, notes=""):
    print(f"Registrando pagamento: card_id={card_id}, payment_method={payment_method}, paid_amount={paid_amount}")
    try:
        data = {
            "card_id": card_id,
            "payment_method": payment_method,
            "paid_amount": paid_amount,
            "notes": notes
        }
        response = requests.post(f"{API_BASE_URL}card-payments", json=data, headers=HEADERS)
        print(f"Resposta do /api/card-payments: {response.status_code}, {response.text}")
        response.raise_for_status()
        payment = response.json()
        receipt_response = requests.get(f"{API_BASE_URL}card-payments/{payment['card_id']}/receipt", headers=HEADERS)
        print(f"Resposta do /api/card-payments/{payment['card_id']}/receipt: {receipt_response.status_code}")
        receipt_response.raise_for_status()
        page.client_storage.remove("comandas")
        return payment, receipt_response.content
    except RequestException as e:
        print(f"Erro ao registrar pagamento: {str(e)}")
        page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao registrar pagamento: {str(e)}"))
        page.snack_bar.open = True
        page.update()
        return None, None

def print_receipt(receipt_data):
    print(f"Iniciando impressão do recibo, data length: {len(receipt_data)}")
    js_code = f"""
    try {{
        var iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        document.body.appendChild(iframe);
        iframe.src = 'data:application/pdf;base64,{receipt_data}';
        iframe.onload = function() {{
            setTimeout(function() {{
                try {{
                    iframe.contentWindow.print();
                    console.log('Print dialog opened');
                    setTimeout(function() {{
                        document.body.removeChild(iframe);
                        console.log('Iframe removed');
                    }}, 1000);
                }} catch (e) {{
                    console.error('Print error: ' + e.message);
                    var blob = new Blob([new Uint8Array(atob('{receipt_data}').split('').map(c => c.charCodeAt(0)))], {{type: 'application/pdf'}});
                    var url = URL.createObjectURL(blob);
                    var win = window.open(url);
                    if (win) {{
                        win.onload = function() {{
                            win.print();
                            setTimeout(function() {{
                                URL.revokeObjectURL(url);
                            }}, 1000);
                        }};
                    }} else {{
                        console.error('Failed to open window');
                    }}
                }}
            }}, 500);
        }};
    }} catch (e) {{
        console.error('Setup error: ' + e.message);
    }}
    """
    try:
        page.run_javascript(js_code)
        print("Comando de impressão enviado ao navegador")
    except Exception as e:
        print(f"Erro ao executar JavaScript para impressão: {str(e)}")
        page.snack_bar = ft.SnackBar(ft.Text("Erro ao iniciar impressão do recibo."))
        page.snack_bar.open = True
        page.update()

def show_main_interface():
    restaurant_id = page.client_storage.get("restaurant_id")
    print(f"Exibindo interface principal: restaurant_id={restaurant_id}")
    if restaurant_id is None:
        print("Erro: restaurant_id não definido em client_storage. Retornando à tela de login.")
        page.snack_bar = ft.SnackBar(ft.Text("Erro: ID do restaurante não definido. Faça login novamente."))
        page.snack_bar.open = True
        show_login_screen(error_message="ID do restaurante não definido. Faça login novamente.")
        return
    global comandas
    comandas = fetch_comandas()
    menu_items = fetch_menu_items()
    if not comandas or not menu_items:
        print("Nenhum item ou comanda disponível")
        page.snack_bar = ft.SnackBar(ft.Text("Nenhum item ou comanda disponível. Adicione itens ao cardápio ou crie comandas."))
        page.snack_bar.open = True

    page.comanda_dropdown = ft.Dropdown(
        label="Selecione a Comanda",
        options=[ft.dropdown.Option(f"Comanda {c['number']} (ID: {c['id']})") for c in comandas if c["is_active"]],
        width=min(page.width * 0.85, 300),
        text_size=14 if page.width < 600 else 16,
        on_change=lambda e: atualizar_tabela_comanda(),
    )
    item_dropdown = ft.Dropdown(
        label="Selecione o Item",
        options=[ft.dropdown.Option(m["name"]) for m in menu_items],
        width=min(page.width * 0.85, 300),
        text_size=14 if page.width < 600 else 16,
    )
    quantidade_field = ft.TextField(
        label="Quantidade",
        value="1.0",
        width=100,
        keyboard_type=ft.KeyboardType.NUMBER,
        text_size=14 if page.width < 600 else 16,
        text_align=ft.TextAlign.CENTER,
    )
    def increase_quantity(e):
        current_value = Decimal(quantidade_field.value.replace(",", ".")) if quantidade_field.value else Decimal("0")
        quantidade_field.value = f"{current_value + 1:.1f}"
        page.update()

    def decrease_quantity(e):
        current_value = Decimal(quantidade_field.value.replace(",", ".")) if quantidade_field.value else Decimal("0")
        if current_value > 0:
            quantidade_field.value = f"{current_value - 1:.1f}"
        page.update()

    quantity_controls = ft.Row(
        [
            ft.IconButton(
                icon=ft.Icons.REMOVE,
                on_click=decrease_quantity,
                bgcolor=ft.Colors.RED_400,
                icon_color=ft.Colors.WHITE,
                icon_size=20 if page.width < 600 else 24,
            ),
            quantidade_field,
            ft.IconButton(
                icon=ft.Icons.ADD,
                on_click=increase_quantity,
                bgcolor=ft.Colors.GREEN_400,
                icon_color=ft.Colors.WHITE,
                icon_size=20 if page.width < 600 else 24,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=5,
    )
    page.metodo_pagamento = ft.Dropdown(
        label="Método de Pagamento",
        options=[
            ft.dropdown.Option(key="CA", text="Dinheiro"),
            ft.dropdown.Option(key="CR", text="Crédito"),
            ft.dropdown.Option(key="DE", text="Débito"),
            ft.dropdown.Option(key="PX", text="Pix"),
            ft.dropdown.Option(key="OT", text="Outro"),
        ],
        value="CA",
        width=min(page.width * 0.85, 200),
        text_size=14 if page.width < 600 else 16,
        on_change=lambda e: atualizar_visibilidade_valor_recebido(),
    )
    page.valor_recebido = ft.TextField(
        label="Valor Recebido (R$)",
        width=min(page.width * 0.85, 150),
        keyboard_type=ft.KeyboardType.NUMBER,
        text_size=14 if page.width < 600 else 16,
        visible=True,
        on_change=lambda e: calcular_troco(),
    )
    page.troco_text = ft.Text("Troco: R$ 0.00", visible=True, size=12 if page.width < 600 else 14)
    page.total_comanda_text = ft.Text("Total: R$ 0.00", size=16 if page.width < 600 else 18, weight=ft.FontWeight.BOLD)

    def adicionar_valor(valor):
        try:
            current_value = Decimal(page.valor_recebido.value.replace(",", ".")) if page.valor_recebido.value else Decimal(0)
            new_value = current_value + Decimal(valor)
            page.valor_recebido.value = f"{new_value:.2f}".replace(".", ",")
            calcular_troco()
            page.update()
        except (InvalidOperation, ValueError):
            page.valor_recebido.value = f"{valor:.2f}".replace(".", ",")
            calcular_troco()
            page.update()

    def zerar_valor():
        page.valor_recebido.value = ""
        page.troco_text.value = "Troco: R$ 0.00"
        page.update()

    valores_botoes = [1, 2, 5, 10, 20, 50, 100, 200, 0.05, 0.10, 0.25, 0.50]
    botoes_valores = ft.ResponsiveRow(
        [
            ft.ElevatedButton(
                text=str(valor),
                on_click=lambda e, v=valor: adicionar_valor(v),
                bgcolor=ft.Colors.BLUE_100,
                color=ft.Colors.BLUE_900,
                width=50 if page.width < 600 else 60,
                height=40 if page.width < 600 else 50,
                col={"xs": 4, "sm": 3, "md": 2},
            ) for valor in valores_botoes
        ] + [
            ft.ElevatedButton(
                text="Zerar",
                on_click=lambda e: zerar_valor(),
                bgcolor=ft.Colors.RED_100,
                color=ft.Colors.RED_900,
                width=50 if page.width < 600 else 60,
                height=40 if page.width < 600 else 50,
                col={"xs": 4, "sm": 3, "md": 2},
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        visible=True,
    )
    page.comanda_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Item")),
            ft.DataColumn(ft.Text("Qtd.")),
            ft.DataColumn(ft.Text("Preço")),
            ft.DataColumn(ft.Text("Subtotal")),
            ft.DataColumn(ft.Text("Ações")),
        ],
        column_spacing=5,
        rows=[],
    )
    loading = ft.ProgressRing(visible=False, width=20 if page.width < 600 else 24, height=20 if page.width < 600 else 24)

    def calcular_totais(comanda):
        total = 0
        for item in comanda["card_items"]:
            subtotal = Decimal(str(item["subtotal"]))
            total += subtotal
        return total

    def atualizar_tabela_comanda():
        print("Atualizando tabela de comanda")
        if not hasattr(page, 'comanda_table') or not hasattr(page, 'total_comanda_text'):
            print("Aviso: comanda_table ou total_comanda_text não definido")
            return
        page.comanda_table.rows.clear()
        total_comanda = 0
        if hasattr(page, 'comanda_dropdown') and page.comanda_dropdown and page.comanda_dropdown.value:
            comanda_id = int(page.comanda_dropdown.value.split("ID: ")[1].strip(")"))
            try:
                response = requests.get(f"{API_BASE_URL}cards/{comanda_id}", headers=HEADERS)
                print(f"Resposta do /api/cards/{comanda_id}: {response.status_code}, {response.text}")
                response.raise_for_status()
                comanda = response.json()
                print(f"Comanda carregada: {comanda}")
            except RequestException as e:
                print(f"Erro ao buscar comanda: {str(e)}")
                page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao buscar comanda: {str(e)}"))
                page.snack_bar.open = True
                page.update()
                return

            for item in comanda["card_items"]:
                print(f"Adicionando item à tabela: {item['menu_item']['name']}, quantidade: {item['quantity']}")
                page.comanda_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(
                                ft.Text(
                                    item["menu_item"]["name"],
                                    size=12 if page.width < 600 else 14,
                                    no_wrap=False,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                )
                            ),
                            ft.DataCell(
                                ft.Text(
                                    f"{float(item['quantity']):.2f}",
                                    size=12 if page.width < 600 else 14,
                                    text_align=ft.TextAlign.CENTER,
                                )
                            ),
                            ft.DataCell(
                                ft.Text(
                                    f"R$ {float(item['price']):.2f}",
                                    size=12 if page.width < 600 else 14,
                                    text_align=ft.TextAlign.RIGHT,
                                )
                            ),
                            ft.DataCell(
                                ft.Text(
                                    f"R$ {float(item['subtotal']):.2f}",
                                    size=12 if page.width < 600 else 14,
                                    text_align=ft.TextAlign.RIGHT,
                                )
                            ),
                            ft.DataCell(
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    tooltip="Remover",
                                    icon_size=16 if page.width < 600 else 20,
                                    on_click=lambda e, item_id=item["id"]: handle_delete_item(comanda_id, item_id)
                                )
                            ),
                        ]
                    )
                )
            total_comanda = sum(float(item['subtotal']) for item in comanda["card_items"])
        page.total_comanda_text.value = f"Total: R$ {total_comanda:.2f}"
        calcular_troco()
        page.update()

    def handle_delete_item(card_id, item_id):
        print(f"Chamando handle_delete_item: card_id={card_id}, item_id={item_id}")
        loading.visible = True
        page.update()
        if delete_card_item(card_id, item_id):
            atualizar_tabela_comanda()
            page.snack_bar = ft.SnackBar(ft.Text("Item removido com sucesso!"))
            page.snack_bar.open = True
        loading.visible = False
        page.update()

    def adicionar_item(e):
        print("Botão Adicionar Item clicado")
        if not hasattr(page, 'comanda_dropdown') or not page.comanda_dropdown.value:
            page.snack_bar = ft.SnackBar(ft.Text("Selecione uma comanda primeiro!"))
            page.snack_bar.open = True
            page.update()
            return

        if item_dropdown.value and quantidade_field.value:
            try:
                quantidade_str = quantidade_field.value.replace(",", ".")
                print(f"Quantidade inserida: {quantidade_str}")
                quantidade = Decimal(quantidade_str)
                if quantidade <= 0:
                    page.snack_bar = ft.SnackBar(ft.Text("Quantidade deve ser maior que 0!"))
                    page.snack_bar.open = True
                    page.update()
                    return

                comanda_id = int(page.comanda_dropdown.value.split("ID: ")[1].strip(")"))
                item = next(m for m in menu_items if m["name"] == item_dropdown.value)
                print(f"Item selecionado: {item['name']}, ID: {item['id']}, Quantidade: {quantidade}")

                loading.visible = True
                page.update()
                result = add_card_item(comanda_id, item["id"], quantidade)
                loading.visible = False
                if result:
                    quantidade_field.value = "1.0"
                    item_dropdown.value = None
                    atualizar_tabela_comanda()
                    page.snack_bar = ft.SnackBar(ft.Text(f"{item['name']} adicionado à comanda!"))
                    page.snack_bar.open = True
                else:
                    page.snack_bar = ft.SnackBar(ft.Text("Falha ao adicionar item. Verifique os logs."))
                    page.snack_bar.open = True
            except (ValueError, InvalidOperation) as e:
                print(f"Erro na validação da quantidade: {str(e)}")
                page.snack_bar = ft.SnackBar(ft.Text("Quantidade inválida! Use números decimais (ex.: 1.5)."))
                page.snack_bar.open = True
            except Exception as e:
                print(f"Erro inesperado ao adicionar item: {str(e)}")
                page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao adicionar item: {str(e)}"))
                page.snack_bar.open = True
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Selecione um item e informe a quantidade!"))
            page.snack_bar.open = True
        page.update()

    def atualizar_visibilidade_valor_recebido():
        print("Atualizando visibilidade do valor recebido")
        if hasattr(page, 'valor_recebido') and hasattr(page, 'troco_text') and hasattr(page, 'metodo_pagamento'):
            is_cash = page.metodo_pagamento.value == "CA"
            is_small_screen = page.width < 600
            page.valor_recebido.visible = is_cash
            page.troco_text.visible = is_cash
            botoes_valores.visible = is_cash and not is_small_screen
            if not page.valor_recebido.visible:
                page.valor_recebido.value = ""
                page.troco_text.value = "Troco: R$ 0.00"
            calcular_troco()
            page.update()

    def calcular_troco():
        print("Calculando troco")
        if hasattr(page, 'metodo_pagamento') and hasattr(page, 'valor_recebido') and hasattr(page, 'comanda_dropdown') and hasattr(page, 'troco_text'):
            if page.metodo_pagamento.value == "CA" and page.valor_recebido.value and page.comanda_dropdown.value:
                try:
                    valor_recebido_decimal = Decimal(page.valor_recebido.value.replace(",", "."))
                    comanda_id = int(page.comanda_dropdown.value.split("ID: ")[1].strip(")"))
                    response = requests.get(f"{API_BASE_URL}cards/{comanda_id}", headers=HEADERS)
                    print(f"Resposta do /api/cards/{comanda_id} (calcular_troco): {response.status_code}, {response.text}")
                    response.raise_for_status()
                    comanda = response.json()
                    total_comanda = sum(float(item['subtotal']) for item in comanda["card_items"])
                    troco = Decimal(valor_recebido_decimal) - Decimal(total_comanda)
                    page.troco_text.value = f"Troco: R$ {troco:.2f}" if troco >= 0 else "Valor insuficiente!"
                except (ValueError, InvalidOperation, RequestException):
                    page.troco_text.value = "Troco: R$ 0.00"
            else:
                page.troco_text.value = "Troco: R$ 0.00"
            page.update()

    def confirmar_pagamento(e):
        print("Botão Confirmar Pagamento clicado")
        if not hasattr(page, 'comanda_dropdown') or not page.comanda_dropdown.value or not hasattr(page, 'metodo_pagamento') or not page.metodo_pagamento.value:
            print("Erro: Comanda ou método de pagamento não selecionado")
            page.snack_bar = ft.SnackBar(ft.Text("Selecione a comanda e o método de pagamento!"))
            page.snack_bar.open = True
            page.update()
            return

        comanda_id = int(page.comanda_dropdown.value.split("ID: ")[1].strip(")"))
        try:
            response = requests.get(f"{API_BASE_URL}cards/{comanda_id}", headers=HEADERS)
            print(f"Resposta do /api/cards/{comanda_id} (confirmar_pagamento): {response.status_code}, {response.text}")
            response.raise_for_status()
            comanda = response.json()
            total_comanda = calcular_totais(comanda)
        except RequestException as e:
            print(f"Erro ao buscar comanda para pagamento: {str(e)}")
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao buscar comanda: {str(e)}"))
            page.snack_bar.open = True
            page.update()
            return

        if page.metodo_pagamento.value == "CA" and (not page.valor_recebido.value or Decimal(page.valor_recebido.value.replace(",", ".")) < total_comanda):
            print("Erro: Valor recebido insuficiente")
            page.snack_bar = ft.SnackBar(ft.Text("Valor recebido insuficiente!"))
            page.snack_bar.open = True
            page.update()
            return

        loading.visible = True
        page.update()
        paid_amount = float(page.valor_recebido.value.replace(",", ".")) if page.metodo_pagamento.value == "CA" and page.valor_recebido.value else None
        try:
            payment, receipt_pdf = create_payment(comanda_id, page.metodo_pagamento.value, paid_amount)
        except Exception as e:
            print(f"Erro ao processar pagamento: {str(e)}")
            loading.visible = False
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao processar pagamento: {str(e)}"))
            page.snack_bar.open = True
            page.update()
            return

        loading.visible = False
        if payment:
            print("Pagamento registrado, preparando SnackBar")
            comandas[:] = fetch_comandas()
            page.comanda_dropdown.options = [ft.dropdown.Option(f"Comanda {c['number']} (ID: {c['id']})") for c in comandas if c["is_active"]]
            page.comanda_dropdown.value = None
            page.comanda_table.rows.clear()
            page.total_comanda_text.value = "Total: R$ 0.00"
            page.metodo_pagamento.value = "CA"
            page.valor_recebido.value = ""
            page.troco_text.value = "Troco: R$ 0.00"
            page.valor_recebido.visible = True
            page.troco_text.visible = True
            botoes_valores.visible = page.width >= 600
            item_dropdown.value = None
            quantidade_field.value = "1.0"

            receipt_data = base64.b64encode(receipt_pdf).decode()
            snack_content = ft.Column([
                ft.Text(f"Pagamento de R$ {total_comanda:.2f} registrado com sucesso!", size=14 if page.width < 600 else 16),
                ft.Row([
                    ft.ElevatedButton(
                        "Baixar Recibo",
                        on_click=lambda e: page.launch_url(f"data:application/pdf;base64,{receipt_data}", web_window_name="_self"),
                        bgcolor=ft.Colors.GREEN_400,
                        color=ft.Colors.WHITE,
                        width=page.width * 0.4 if page.width < 600 else 150,
                    ),
                    ft.ElevatedButton(
                        "Imprimir Recibo",
                        on_click=lambda e: print_receipt(receipt_data),
                        bgcolor=ft.Colors.BLUE_400,
                        color=ft.Colors.WHITE,
                        width=page.width * 0.4 if page.width < 600 else 150,
                    ),
                ], spacing=5, alignment=ft.MainAxisAlignment.CENTER, wrap=True),
            ], spacing=5) if page.width < 600 else ft.Row([
                ft.Text(f"Pagamento de R$ {total_comanda:.2f} registrado com sucesso!", size=16),
                ft.ElevatedButton(
                    "Baixar Recibo",
                    on_click=lambda e: page.launch_url(f"data:application/pdf;base64,{receipt_data}", web_window_name="_self"),
                    bgcolor=ft.Colors.GREEN_400,
                    color=ft.Colors.WHITE,
                    width=150,
                ),
                ft.ElevatedButton(
                    "Imprimir Recibo",
                    on_click=lambda e: print_receipt(receipt_data),
                    bgcolor=ft.Colors.BLUE_400,
                    color=ft.Colors.WHITE,
                    width=150,
                ),
            ], spacing=10, alignment=ft.MainAxisAlignment.CENTER)

            if page.metodo_pagamento.value == "PX":
                pix_key = fetch_restaurant_pix_key()
                if pix_key:
                    try:
                        response = requests.get(f"{API_BASE_URL}restaurants/{page.client_storage.get('restaurant_id')}", headers=HEADERS)
                        restaurant_data = response.json()
                        restaurant_name = restaurant_data.get("name", "Restaurante")
                        qr_code_data = generate_pix_qr_code(pix_key, total_comanda, restaurant_name)
                        qr_code_base64 = base64.b64encode(qr_code_data).decode()
                        qr_code_image = ft.Image(
                            src_base64=qr_code_base64,
                            width=200,
                            height=200,
                        )
                        dialog = ft.AlertDialog(
                            title=ft.Text("QR Code para Pagamento Pix"),
                            content=ft.Column([
                                qr_code_image,
                                ft.Text(f"Chave Pix: {pix_key}"),
                                ft.Text(f"Valor: R$ {total_comanda:.2f}"),
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            actions=[
                                ft.TextButton("Fechar", on_click=lambda e: page.close_dialog())
                            ],
                            actions_alignment=ft.MainAxisAlignment.END,
                        )
                        page.dialog = dialog
                        dialog.open = True
                        page.update()
                    except Exception as e:
                        print(f"Erro ao gerar QR code Pix: {str(e)}")
                        snack_content.controls.append(ft.Text(f"Erro ao gerar QR code Pix: {str(e)}", color=ft.Colors.RED_600))
                else:
                    snack_content.controls.append(ft.Text("Chave Pix não disponível.", color=ft.Colors.RED_600))

            page.snack_bar = ft.SnackBar(
                content=snack_content,
                duration=10000,
                width=page.width * 0.9 if page.width < 600 else 600,
                padding=10,
                bgcolor=ft.Colors.GREY_800,
            )
            print(f"Exibindo SnackBar com botões de recibo, open={page.snack_bar.open}")
            page.snack_bar.open = True
            page.update()
        else:
            print("Falha ao registrar pagamento")
            page.snack_bar = ft.SnackBar(ft.Text("Falha ao registrar pagamento. Verifique os logs."))
            page.snack_bar.open = True
            page.update()

    def atualizar_comandas_periodicamente():
        restaurant_id = page.client_storage.get("restaurant_id")
        print(f"Atualizando comandas periodicamente... restaurant_id={restaurant_id}")
        if restaurant_id is None:
            print("Erro: restaurant_id não definido. Retornando à tela de login.")
            show_login_screen(error_message="Sessão inválida. Faça login novamente.")
            return
        try:
            comandas[:] = fetch_comandas()
            if hasattr(page, 'comanda_dropdown') and page.comanda_dropdown:
                page.comanda_dropdown.options = [ft.dropdown.Option(f"Comanda {c['number']} (ID: {c['id']})") for c in comandas if c["is_active"]]
            page.update()
            threading.Timer(10.0, atualizar_comandas_periodicamente).start()
        except Exception as e:
            print(f"Erro ao atualizar comandas: {str(e)}")
            if "Faça login novamente" in str(e) or "Autenticação necessária" in str(e):
                show_login_screen(error_message="Sessão expirada. Faça login novamente.")
            else:
                page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao atualizar comandas: {str(e)}"))
                page.snack_bar.open = True
                page.update()
                threading.Timer(10.0, atualizar_comandas_periodicamente).start()

    threading.Timer(10.0, atualizar_comandas_periodicamente).start()

    main_layout = ft.Column(
        [
            ft.Row(
                [
                    ft.Text(
                        "Sistema de Caixa - Pagamento de Comandas",
                        size=18 if page.width < 600 else 24,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    loading,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Divider(),
            ft.ResponsiveRow(
                [
                    ft.Column(
                        col={"xs": 12, "sm": 6, "md": 4},
                        controls=[page.comanda_dropdown],
                    ),
                    ft.Column(
                        col={"xs": 12, "sm": 6, "md": 4},
                        controls=[
                            ft.ElevatedButton(
                                "Adicionar Item",
                                on_click=adicionar_item,
                                bgcolor=ft.Colors.GREEN_400,
                                color=ft.Colors.WHITE,
                                width=page.width * 0.85 if page.width < 600 else 150,
                                height=40 if page.width < 600 else 50,
                            ),
                        ],
                    ),
                    ft.Column(
                        col={"xs": 12, "sm": 6, "md": 4},
                        controls=[
                            ft.ElevatedButton(
                                "Criar Comanda",
                                on_click=lambda e: create_comanda(),
                                bgcolor=ft.Colors.BLUE_400,
                                color=ft.Colors.WHITE,
                                width=page.width * 0.85 if page.width < 600 else 150,
                                height=40 if page.width < 600 else 50,
                            ),
                        ],
                    ),
                    ft.Column(
                        col={"xs": 12, "sm": 6, "md": 4},
                        controls=[
                            ft.ElevatedButton(
                                "Atualizar Comandas",
                                on_click=lambda e: atualizar_comandas_periodicamente(),
                                bgcolor=ft.Colors.BLUE_400,
                                color=ft.Colors.WHITE,
                                width=page.width * 0.85 if page.width < 600 else 150,
                                height=40 if page.width < 600 else 50,
                            ),
                        ],
                    ),
                ],
            ),
            ft.ResponsiveRow(
                [
                    ft.Column(
                        col={"xs": 12, "sm": 6, "md": 4},
                        controls=[item_dropdown],
                    ),
                    ft.Column(
                        col={"xs": 12, "sm": 6, "md": 4},
                        controls=[quantity_controls],
                    ),
                ],
            ),
            ft.Container(
                content=ft.ListView(
                    controls=[page.comanda_table],
                    auto_scroll=True,
                    expand=True,
                ),
                height=page.height * 0.3 if page.width < 600 else page.height * 0.4,
                border=ft.border.all(1, ft.Colors.GREY_400),
                margin=ft.margin.only(top=10),
            ),
            ft.Row(
                [page.total_comanda_text],
                alignment=ft.MainAxisAlignment.END,
            ),
            ft.Text(
                "Pagamento",
                size=14 if page.width < 600 else 18,
                weight=ft.FontWeight.BOLD,
            ),
            ft.ResponsiveRow(
                [
                    ft.Column(
                        col={"xs": 12, "sm": 6, "md": 3},
                        controls=[page.metodo_pagamento],
                    ),
                    ft.Column(
                        col={"xs": 12, "sm": 6, "md": 3},
                        controls=[page.valor_recebido],
                    ),
                    ft.Column(
                        col={"xs": 12, "sm": 6, "md": 3},
                        controls=[page.troco_text],
                    ),
                ],
            ),
            botoes_valores,
            ft.Row(
                [
                    ft.ElevatedButton(
                        "Confirmar Pagamento",
                        on_click=confirmar_pagamento,
                        bgcolor=ft.Colors.GREEN_400,
                        color=ft.Colors.WHITE,
                        width=page.width * 0.85 if page.width < 600 else 200,
                        height=40 if page.width < 600 else 50,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ],
        scroll=ft.ScrollMode.AUTO,
        spacing=10,
    )

    page.controls.clear()
    page.add(
        ft.Container(
            content=main_layout,
            alignment=ft.alignment.top_center,
            padding=ft.padding.only(left=5, right=5, top=10, bottom=10),
            width=page.width,
            expand=True,
        )
    )
    atualizar_tabela_comanda()
    page.update()

ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=8500)
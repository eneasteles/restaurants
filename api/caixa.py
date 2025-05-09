import flet as ft
from decimal import Decimal
import requests
from requests.exceptions import RequestException
import base64
from io import BytesIO

def main(page: ft.Page):
    page.title = "Caixa do Restaurante - Pagamentos"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window_width = 900
    page.window_height = 700
    page.bgcolor = ft.Colors.GREY_100

    # Configuração da API
    API_BASE_URL = "http://localhost:8000/api/"
    HEADERS = {}
    RESTAURANT_ID = None

    # Função de login
    def login(username, password):
        try:
            response = requests.post(f"{API_BASE_URL}token/", data={"username": username, "password": password})
            response.raise_for_status()
            data = response.json()
            token = data.get("access")
            user_response = requests.get(f"{API_BASE_URL}user-profile", headers={"Authorization": f"Bearer {token}"})
            user_response.raise_for_status()
            profile = user_response.json()
            return {"Authorization": f"Bearer {token}"}, profile["restaurant_id"]
        except RequestException as e:
            return None, None, str(e)

    # Tela de autenticação
    def show_login_screen():
        username_field = ft.TextField(
            label="Usuário",
            prefix_icon=ft.icons.PERSON,
            width=300,
            border_radius=10,
            border_color=ft.Colors.GREY_400,
        )
        password_field = ft.TextField(
            label="Senha",
            prefix_icon=ft.icons.LOCK,
            password=True,
            can_reveal_password=True,
            width=300,
            border_radius=10,
            border_color=ft.Colors.GREY_400,
        )
        error_message = ft.Text("", color=ft.Colors.RED_600, visible=False)
        loading = ft.ProgressRing(visible=False, width=24, height=24)

        def handle_login(e):
            error_message.visible = False
            loading.visible = True
            page.update()

            if not username_field.value or not password_field.value:
                error_message.value = "Por favor, preencha usuário e senha."
                error_message.visible = True
                loading.visible = False
                page.update()
                return

            headers, restaurant_id, error = login(username_field.value, password_field.value)
            loading.visible = False

            if headers and restaurant_id:
                global HEADERS, RESTAURANT_ID
                HEADERS = headers
                RESTAURANT_ID = restaurant_id
                page.controls.clear()
                show_main_interface()
            else:
                error_message.value = "Credenciais inválidas ou erro de conexão." if not error else f"Erro: {error}"
                error_message.visible = True
            page.update()

        login_container = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Sistema de Caixa",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_900,
                    ),
                    ft.Text(
                        "Faça login para continuar",
                        size=16,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    username_field,
                    password_field,
                    error_message,
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                content=ft.Row(
                                    [
                                        ft.Text("Entrar", size=16, weight=ft.FontWeight.BOLD),
                                        loading,
                                    ],
                                    spacing=10,
                                ),
                                bgcolor=ft.Colors.GREEN_400,
                                color=ft.Colors.WHITE,
                                width=300,
                                height=50,
                                on_click=handle_login,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=15,
            ),
            width=400,
            padding=30,
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

    # Funções para chamadas à API
    def fetch_comandas():
        comandas = page.client_storage.get("comandas")
        if comandas:
            return comandas
        try:
            response = requests.get(f"{API_BASE_URL}cards", headers=HEADERS)
            response.raise_for_status()
            comandas = response.json()
            page.client_storage.set("comandas", comandas)
            return comandas
        except RequestException as e:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao buscar comandas: {str(e)}"))
            page.snack_bar.open = True
            page.update()
            return []

    def fetch_menu_items():
        menu_items = page.client_storage.get("menu_items")
        if menu_items:
            return menu_items
        try:
            response = requests.get(f"{API_BASE_URL}menu-items", headers=HEADERS)
            response.raise_for_status()
            menu_items = response.json()
            page.client_storage.set("menu_items", menu_items)
            return menu_items
        except RequestException as e:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao buscar itens do cardápio: {str(e)}"))
            page.snack_bar.open = True
            page.update()
            return []

    def add_card_item(card_id, menu_item_id, quantity):
        try:
            data = {"menu_item_id": menu_item_id, "quantity": quantity}
            response = requests.post(f"{API_BASE_URL}cards/{card_id}/items", json=data, headers=HEADERS)
            response.raise_for_status()
            page.client_storage.remove("comandas")  # Invalidar cache
            return response.json()
        except RequestException as e:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao adicionar item: {str(e)}"))
            page.snack_bar.open = True
            page.update()
            return None

    def delete_card_item(card_id, item_id):
        try:
            response = requests.delete(f"{API_BASE_URL}cards/{card_id}/items/{item_id}", headers=HEADERS)
            response.raise_for_status()
            page.client_storage.remove("comandas")  # Invalidar cache
            return True
        except RequestException as e:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao remover item: {str(e)}"))
            page.snack_bar.open = True
            page.update()
            return False

    def create_payment(card_id, payment_method, paid_amount=None, notes=""):
        try:
            data = {
                "card_id": card_id,
                "payment_method": payment_method,
                "paid_amount": paid_amount,
                "notes": notes
            }
            response = requests.post(f"{API_BASE_URL}card-payments", json=data, headers=HEADERS)
            response.raise_for_status()
            payment = response.json()
            # Obter recibo PDF
            receipt_response = requests.get(f"{API_BASE_URL}card-payments/{payment['card_id']}/receipt", headers=HEADERS)
            receipt_response.raise_for_status()
            page.client_storage.remove("comandas")  # Invalidar cache
            return payment, receipt_response.content
        except RequestException as e:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao registrar pagamento: {str(e)}"))
            page.snack_bar.open = True
            page.update()
            return None, None

    # Interface principal
    def show_main_interface():
        comandas = fetch_comandas()
        menu_items = fetch_menu_items()

        comanda_dropdown = ft.Dropdown(
            label="Selecione a Comanda",
            options=[ft.dropdown.Option(f"Comanda {c['number']} (ID: {c['id']})") for c in comandas if c["is_active"]],
            width=300,
            on_change=lambda e: atualizar_tabela_comanda(),
        )
        item_dropdown = ft.Dropdown(
            label="Selecione o Item",
            options=[ft.dropdown.Option(m["name"]) for m in menu_items],
            width=300,
        )
        quantidade_field = ft.TextField(
            label="Quantidade",
            value="1",
            width=100,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        metodo_pagamento = ft.Dropdown(
            label="Método de Pagamento",
            options=[
                ft.dropdown.Option(key="CA", text="Dinheiro"),
                ft.dropdown.Option(key="CR", text="Crédito"),
                ft.dropdown.Option(key="DE", text="Débito"),
                ft.dropdown.Option(key="PX", text="Pix"),
                ft.dropdown.Option(key="OT", text="Outro"),
            ],
            width=200,
            on_change=lambda e: atualizar_visibilidade_valor_recebido(),
        )
        valor_recebido = ft.TextField(
            label="Valor Recebido (R$)",
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER,
            visible=False,
            on_change=lambda e: calcular_troco(),
        )
        troco_text = ft.Text("Troco: R$ 0.00", visible=False)
        total_comanda_text = ft.Text("Total: R$ 0.00", size=20, weight=ft.FontWeight.BOLD)

        comanda_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Item")),
                ft.DataColumn(ft.Text("Quantidade")),
                ft.DataColumn(ft.Text("Preço Unitário")),
                ft.DataColumn(ft.Text("Subtotal")),
                ft.DataColumn(ft.Text("Ações")),
            ],
            rows=[],
        )

        loading = ft.ProgressRing(visible=False)

        def calcular_totais(comanda):
            total = 0
            for item in comanda["card_items"]:
                subtotal = Decimal(str(item["subtotal"]))
                total += subtotal
            return total

        def atualizar_tabela_comanda():
            comanda_table.rows.clear()
            total_comanda = 0
            if comanda_dropdown.value:
                comanda_id = int(comanda_dropdown.value.split("ID: ")[1].strip(")"))
                try:
                    response = requests.get(f"{API_BASE_URL}cards/{comanda_id}", headers=HEADERS)
                    response.raise_for_status()
                    comanda = response.json()
                except RequestException as e:
                    page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao buscar comanda: {str(e)}"))
                    page.snack_bar.open = True
                    page.update()
                    return

                for item in comanda["card_items"]:
                    comanda_table.rows.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(item["menu_item"]["name"])),
                                ft.DataCell(ft.Text(str(item["quantity"]))),
                                ft.DataCell(ft.Text(f"R$ {item['price']:.2f}")),
                                ft.DataCell(ft.Text(f"R$ {item['subtotal']:.2f}")),
                                ft.DataCell(
                                    ft.IconButton(
                                        icon=ft.icons.DELETE,
                                        tooltip="Remover",
                                        on_click=lambda e, item_id=item["id"]: handle_delete_item(comanda_id, item_id)
                                    )
                                ),
                            ]
                        )
                    )
                total_comanda = calcular_totais(comanda)
            total_comanda_text.value = f"Total: R$ {total_comanda:.2f}"
            calcular_troco()
            page.update()

        def handle_delete_item(card_id, item_id):
            loading.visible = True
            page.update()
            if delete_card_item(card_id, item_id):
                atualizar_tabela_comanda()
                page.snack_bar = ft.SnackBar(ft.Text("Item removido com sucesso!"))
                page.snack_bar.open = True
            loading.visible = False
            page.update()

        def adicionar_item(e):
            if not comanda_dropdown.value:
                page.snack_bar = ft.SnackBar(ft.Text("Selecione uma comanda primeiro!"))
                page.snack_bar.open = True
                page.update()
                return

            if item_dropdown.value and quantidade_field.value:
                try:
                    quantidade = int(quantidade_field.value)
                    if quantidade <= 0:
                        page.snack_bar = ft.SnackBar(ft.Text("Quantidade deve ser maior que 0!"))
                        page.snack_bar.open = True
                        page.update()
                        return

                    comanda_id = int(comanda_dropdown.value.split("ID: ")[1].strip(")"))
                    item = next(m for m in menu_items if m["name"] == item_dropdown.value)

                    loading.visible = True
                    page.update()
                    result = add_card_item(comanda_id, item["id"], quantidade)
                    loading.visible = False
                    if result:
                        quantidade_field.value = "1"
                        item_dropdown.value = None
                        atualizar_tabela_comanda()
                        page.snack_bar = ft.SnackBar(ft.Text(f"{item['name']} adicionado à comanda!"))
                        page.snack_bar.open = True
                except ValueError:
                    page.snack_bar = ft.SnackBar(ft.Text("Quantidade inválida!"))
                    page.snack_bar.open = True
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Selecione um item e informe a quantidade!"))
                page.snack_bar.open = True
            page.update()

        def atualizar_visibilidade_valor_recebido():
            valor_recebido.visible = metodo_pagamento.value == "CA"
            troco_text.visible = metodo_pagamento.value == "CA"
            if not valor_recebido.visible:
                valor_recebido.value = ""
                troco_text.value = "Troco: R$ 0.00"
            calcular_troco()
            page.update()

        def calcular_troco():
            if metodo_pagamento.value == "CA" and valor_recebido.value and comanda_dropdown.value:
                try:
                    valor_recebido_decimal = Decimal(valor_recebido.value.replace(",", "."))
                    comanda_id = int(comanda_dropdown.value.split("ID: ")[1].strip(")"))
                    response = requests.get(f"{API_BASE_URL}cards/{comanda_id}", headers=HEADERS)
                    response.raise_for_status()
                    comanda = response.json()
                    total_comanda = calcular_totais(comanda)
                    troco = valor_recebido_decimal - total_comanda
                    troco_text.value = f"Troco: R$ {troco:.2f}" if troco >= 0 else "Valor insuficiente!"
                except (ValueError, Decimal.InvalidOperation, RequestException):
                    troco_text.value = "Troco: R$ 0.00"
            else:
                troco_text.value = "Troco: R$ 0.00"
            page.update()

        def confirmar_pagamento(e):
            if not comanda_dropdown.value or not metodo_pagamento.value:
                page.snack_bar = ft.SnackBar(ft.Text("Selecione a comanda e o método de pagamento!"))
                page.snack_bar.open = True
                page.update()
                return

            comanda_id = int(comanda_dropdown.value.split("ID: ")[1].strip(")"))
            response = requests.get(f"{API_BASE_URL}cards/{comanda_id}", headers=HEADERS)
            response.raise_for_status()
            comanda = response.json()
            total_comanda = calcular_totais(comanda)

            if metodo_pagamento.value == "CA" and (not valor_recebido.value or Decimal(valor_recebido.value.replace(",", ".")) < total_comanda):
                page.snack_bar = ft.SnackBar(ft.Text("Valor recebido insuficiente!"))
                page.snack_bar.open = True
                page.update()
                return

            loading.visible = True
            page.update()
            paid_amount = float(valor_recebido.value.replace(",", ".")) if metodo_pagamento.value == "CA" and valor_recebido.value else None
            payment, receipt_pdf = create_payment(comanda_id, metodo_pagamento.value, paid_amount)
            loading.visible = False
            if payment:
                comandas[:] = fetch_comandas()
                comanda_dropdown.options = [ft.dropdown.Option(f"Comanda {c['number']} (ID: {c['id']})") for c in comandas if c["is_active"]]
                comanda_dropdown.value = None
                comanda_table.rows.clear()
                total_comanda_text.value = "Total: R$ 0.00"
                metodo_pagamento.value = None
                valor_recebido.value = ""
                troco_text.value = "Troco: R$ 0.00"
                valor_recebido.visible = False
                troco_text.visible = False
                item_dropdown.value = None
                quantidade_field.value = "1"

                # Exibir botão para download do recibo
                receipt_data = base64.b64encode(receipt_pdf).decode()
                page.snack_bar = ft.SnackBar(
                    content=ft.Row([
                        ft.Text(f"Pagamento de R$ {total_comanda:.2f} registrado com sucesso!"),
                        ft.ElevatedButton(
                            "Baixar Recibo",
                            on_click=lambda e: page.launch_url(f"data:application/pdf;base64,{receipt_data}", web_window_name="_self")
                        )
                    ])
                )
                page.snack_bar.open = True
            page.update()

        main_layout = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Sistema de Caixa - Pagamento de Comandas", size=24, weight=ft.FontWeight.BOLD),
                        loading,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Divider(),
                ft.Row(
                    [
                        comanda_dropdown,
                        item_dropdown,
                        quantidade_field,
                        ft.ElevatedButton("Adicionar Item", on_click=adicionar_item),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=20,
                ),
                ft.Container(
                    content=comanda_table,
                    height=300,
                    expand=True,
                    border=ft.border.all(1, ft.Colors.GREY_400),
                    margin=ft.margin.only(top=10),
                ),
                ft.Row(
                    [
                        total_comanda_text,
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
                ft.Row(
                    [
                        ft.Text("Pagamento", size=18, weight=ft.FontWeight.BOLD),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Row(
                    [
                        metodo_pagamento,
                        valor_recebido,
                        troco_text,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=20,
                ),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "Confirmar Pagamento",
                            on_click=confirmar_pagamento,
                            bgcolor=ft.Colors.GREEN_400,
                            color=ft.Colors.WHITE,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            spacing=20,
        )

        page.controls.clear()
        page.add(main_layout)

    # Iniciar com a tela de login
    show_login_screen()

ft.app(target=main)
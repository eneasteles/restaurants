import flet as ft
from decimal import Decimal

def main(page: ft.Page):
    page.title = "Caixa do Restaurante - Pagamentos"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window_width = 900
    page.window_height = 700

    # Dados simulados (em um sistema real, seriam buscados via API)
    menu_items = [
        {"id": 1, "name": "Pizza Margherita", "price": 45.00},
        {"id": 2, "name": "Hambúrguer Clássico", "price": 25.00},
        {"id": 3, "name": "Refrigerante 350ml", "price": 6.00},
        {"id": 4, "name": "Batata Frita", "price": 15.00},
    ]

    comandas = [
        {
            "id": 1,
            "number": 101,
            "is_active": True,
            "card_items": [
                {"menu_item": {"id": 1, "name": "Pizza Margherita", "price": 45.00}, "quantity": 2, "price": 45.00},
                {"menu_item": {"id": 3, "name": "Refrigerante 350ml", "price": 6.00}, "quantity": 3, "price": 6.00},
            ],
        },
        {
            "id": 2,
            "number": 102,
            "is_active": True,
            "card_items": [
                {"menu_item": {"id": 2, "name": "Hambúrguer Clássico", "price": 25.00}, "quantity": 1, "price": 25.00},
            ],
        },
    ]

    # Componentes da interface
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

    # Tabela para exibir itens da comanda
    comanda_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Item")),
            ft.DataColumn(ft.Text("Quantidade")),
            ft.DataColumn(ft.Text("Preço Unitário")),
            ft.DataColumn(ft.Text("Subtotal")),
        ],
        rows=[],
    )

    # Função para calcular o subtotal e total da comanda
    def calcular_totais(comanda):
        total = 0
        for item in comanda["card_items"]:
            subtotal = Decimal(str(item["price"])) * item["quantity"]
            total += subtotal
        return total

    # Função para atualizar a tabela da comanda
    def atualizar_tabela_comanda():
        comanda_table.rows.clear()
        total_comanda = 0
        if comanda_dropdown.value:
            comanda_id = int(comanda_dropdown.value.split("ID: ")[1].strip(")"))
            comanda = next(c for c in comandas if c["id"] == comanda_id)
            for item in comanda["card_items"]:
                subtotal = Decimal(str(item["price"])) * item["quantity"]
                comanda_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(item["menu_item"]["name"])),
                            ft.DataCell(ft.Text(str(item["quantity"]))),
                            ft.DataCell(ft.Text(f"R$ {item['price']:.2f}")),
                            ft.DataCell(ft.Text(f"R$ {subtotal:.2f}")),
                        ]
                    )
                )
            total_comanda = calcular_totais(comanda)
        total_comanda_text.value = f"Total: R$ {total_comanda:.2f}"
        calcular_troco()
        page.update()

    # Função para adicionar item à comanda
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
                comanda = next(c for c in comandas if c["id"] == comanda_id)
                item = next(m for m in menu_items if m["name"] == item_dropdown.value)

                # Adicionar item à comanda
                comanda["card_items"].append(
                    {
                        "menu_item": {"id": item["id"], "name": item["name"], "price": item["price"]},
                        "quantity": quantidade,
                        "price": item["price"],
                    }
                )

                # Simular atualização de estoque (em produção, o sinal faria isso)
                # Aqui, uma API chamaria Stock.objects.update(quantity=F('quantity') - quantidade)
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

    # Função para atualizar visibilidade do campo de valor recebido
    def atualizar_visibilidade_valor_recebido():
        valor_recebido.visible = metodo_pagamento.value == "CA"
        troco_text.visible = metodo_pagamento.value == "CA"
        if not valor_recebido.visible:
            valor_recebido.value = ""
            troco_text.value = "Troco: R$ 0.00"
        calcular_troco()
        page.update()

    # Função para calcular o troco
    def calcular_troco():
        if metodo_pagamento.value == "CA" and valor_recebido.value and comanda_dropdown.value:
            try:
                valor_recebido_decimal = Decimal(valor_recebido.value.replace(",", "."))
                comanda_id = int(comanda_dropdown.value.split("ID: ")[1].strip(")"))
                comanda = next(c for c in comandas if c["id"] == comanda_id)
                total_comanda = calcular_totais(comanda)
                troco = valor_recebido_decimal - total_comanda
                troco_text.value = f"Troco: R$ {troco:.2f}" if troco >= 0 else "Valor insuficiente!"
            except (ValueError, Decimal.InvalidOperation):
                troco_text.value = "Troco: R$ 0.00"
        else:
            troco_text.value = "Troco: R$ 0.00"
        page.update()

    # Função para confirmar o pagamento
    def confirmar_pagamento(e):
        if not comanda_dropdown.value or not metodo_pagamento.value:
            page.snack_bar = ft.SnackBar(ft.Text("Selecione a comanda e o método de pagamento!"))
            page.snack_bar.open = True
            page.update()
            return

        comanda_id = int(comanda_dropdown.value.split("ID: ")[1].strip(")"))
        comanda = next(c for c in comandas if c["id"] == comanda_id)
        total_comanda = calcular_totais(comanda)

        if metodo_pagamento.value == "CA" and (not valor_recebido.value or Decimal(valor_recebido.value.replace(",", ".")) < total_comanda):
            page.snack_bar = ft.SnackBar(ft.Text("Valor recebido insuficiente!"))
            page.snack_bar.open = True
            page.update()
            return

        # Simular salvamento do pagamento (em um sistema real, enviaria para a API)
        pagamento = {
            "restaurant_id": 1,  # Simulado
            "card_id": comanda_id,
            "amount": float(total_comanda),
            "payment_method": metodo_pagamento.value,
            "paid_amount": float(valor_recebido.value.replace(",", ".")) if metodo_pagamento.value == "CA" and valor_recebido.value else None,
            "change_amount": float(Decimal(valor_recebido.value.replace(",", ".")) - total_comanda) if metodo_pagamento.value == "CA" and valor_recebido.value else None,
        }

        # Marcar comanda como inativa
        comanda["is_active"] = False
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

        page.snack_bar = ft.SnackBar(ft.Text(f"Pagamento de R$ {total_comanda:.2f} registrado com sucesso!"))
        page.snack_bar.open = True
        page.update()

    # Layout da página
    page.add(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Sistema de Caixa - Pagamento de Comandas", size=24, weight=ft.FontWeight.BOLD),
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
                    border=ft.border.all(1, ft.colors.GREY_400),
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
                            bgcolor=ft.colors.GREEN_400,
                            color=ft.colors.WHITE,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            spacing=20,
        )
    )

ft.app(target=main)
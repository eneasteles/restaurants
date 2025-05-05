import flet as ft
import requests

API_BASE = "http://localhost:8000/api"

def main(page: ft.Page):
    page.title = "Garçom - Comandas"
    page.scroll = ft.ScrollMode.AUTO
    page.window_width = 700
    page.window_height = 800

    codigo_input = ft.TextField(label="Código do Restaurante", password=True, can_reveal_password=True)
    aviso = ft.Text(color="red")
    cards_container = ft.Column()
    menu_items_dropdown = ft.Dropdown(label="Item", options=[])
    quantidade_input = ft.TextField(label="Quantidade", value="1", width=100)
    nova_comanda_input = ft.TextField(label="Número da nova comanda", width=150)
    card_selecionado_id = None

    def carregar_menu_items():
        try:
            response = requests.get(f"{API_BASE}/menu-items/", params={"codigo": codigo_input.value.strip()})
            if response.status_code == 200:
                dados = response.json().get("items", [])
                menu_items_dropdown.options = [
                    ft.dropdown.Option(str(item["id"]), item["name"]) for item in dados
                ]
        except Exception as e:
            aviso.value = f"Erro ao carregar itens: {e}"

    def carregar_comandas():
        aviso.value = ""
        cards_container.controls.clear()
        try:
            r = requests.get(f"{API_BASE}/cards/", params={"codigo": codigo_input.value.strip()})
            if r.status_code != 200:
                aviso.value = "Código inválido. 23"
                page.update()
                return
            cards = r.json().get("cards", [])
            if not cards:
                cards_container.controls.append(ft.Text("Nenhuma comanda aberta."))
            for card in cards:
                items_text = "\n".join([
                    f"- {i['menu_item_name']} x{i['quantity']}" for i in card["itens"]
                ]) or "Sem itens"
                card_ui = ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(f"Comanda {card['number']}", size=20, weight="bold"),
                            ft.Text(items_text),
                            ft.ElevatedButton("Selecionar", on_click=lambda e, cid=card["id"]: selecionar_card(cid))
                        ])
                    )
                )
                cards_container.controls.append(card_ui)
            page.update()
        except Exception as e:
            aviso.value = f"Erro ao buscar comandas: {e}"

    def selecionar_card(cid):
        nonlocal card_selecionado_id
        card_selecionado_id = cid
        aviso.value = f"Comanda {cid} selecionada para adicionar itens"
        page.update()

    def abrir_comanda(e):
        try:
            r = requests.post(
                f"{API_BASE}/cards/abrir/",
                params={"codigo": codigo_input.value.strip()},
                json={"number": int(nova_comanda_input.value.strip())}
            )
            if r.status_code == 200:
                nova_comanda_input.value = ""
                carregar_comandas()
            else:
                aviso.value = "Erro ao abrir comanda."
        except Exception as ex:
            aviso.value = f"Erro: {ex}"
        page.update()

    def adicionar_item(e):
        if not card_selecionado_id:
            aviso.value = "Selecione uma comanda."
            page.update()
            return
        try:
            payload = {
                "card_id": card_selecionado_id,
                "menu_item_id": int(menu_items_dropdown.value),
                "quantity": int(quantidade_input.value)
            }
            r = requests.post(
                f"{API_BASE}/cards/adicionar-item/",
                params={"codigo": codigo_input.value.strip()},
                json=payload
            )
            if r.status_code == 200:
                aviso.value = "Item adicionado com sucesso!"
                carregar_comandas()
            else:
                aviso.value = "Erro ao adicionar item."
        except Exception as ex:
            aviso.value = f"Falha: {ex}"
        page.update()

    def entrar(e):
        if not codigo_input.value.strip():
            aviso.value = "Informe o código do restaurante."
            return
        carregar_menu_items()
        carregar_comandas()
        page.controls.clear()
        page.add(
            ft.Text("Painel do Garçom", size=28, weight="bold"),
            aviso,
            ft.Row([nova_comanda_input, ft.ElevatedButton("Abrir Comanda", on_click=abrir_comanda)]),
            ft.ElevatedButton("Atualizar Comandas", on_click=lambda e: carregar_comandas()),
            cards_container,
            ft.Text("Adicionar item à comanda selecionada:", weight="bold"),
            ft.Row([menu_items_dropdown, quantidade_input]),
            ft.ElevatedButton("Adicionar Item", on_click=adicionar_item)
        )
        page.update()

    page.add(
        ft.Text("Acesso do Garçom", size=30, weight="bold"),
        codigo_input,
        ft.ElevatedButton("Entrar", icon=ft.icons.LOGIN, on_click=entrar),
        aviso
    )

# ✅ Esta linha garante que o app abre no navegador
ft.app(target=main, view=ft.WEB_BROWSER)

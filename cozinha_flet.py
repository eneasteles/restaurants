import flet as ft
import requests

API_BASE = "http://localhost:8000/api"

def main(page: ft.Page):
    page.title = "Painel da Cozinha"
    page.scroll = ft.ScrollMode.AUTO

    codigo_restaurante = ft.TextField(label="Código do Restaurante", password=True, can_reveal_password=True)
    itens_container = ft.Column()
    aviso = ft.Text(color="red")

    def carregar_itens():
        try:
            response = requests.get(f"{API_BASE}/kitchen/", params={"codigo": codigo_restaurante.value})
            if response.status_code == 404:
                aviso.value = "Código inválido."
                return None
            elif response.status_code != 200:
                aviso.value = f"Erro: {response.status_code}"
                return None
            return response.json().get("items", [])
        except Exception as e:
            aviso.value = f"Erro de conexão: {e}"
            return None


    def marcar_como_pronto(item_id):
        try:
            response = requests.post(
                f"{API_BASE}/kitchen/mark-ready/",
                params={"codigo": codigo_restaurante.value},
                json={"id": item_id}
            )
            return response.status_code == 200
        except Exception as e:
            aviso.value = f"Erro ao marcar como pronto: {e}"
            return False

    def atualizar_lista(e=None):
        aviso.value = ""
        itens_container.controls.clear()
        itens = carregar_itens()
        if not itens:
            itens_container.controls.append(ft.Text("Nenhum item pendente.", size=20))
        else:
            for item in itens:
                linha = ft.Row([
                    ft.Text(f"Comanda {item['card_number']}", width=120),
                    ft.Text(f"{item['menu_item_name']} x{item['quantity']}", expand=True),
                    ft.ElevatedButton("Pronto", on_click=lambda e, id=item['id']: marcar_e_atualizar(id))
                ])
                itens_container.controls.append(linha)
        page.update()

    def marcar_e_atualizar(item_id):
        if marcar_como_pronto(item_id):
            atualizar_lista()

    def confirmar_codigo(e):
        aviso.value = ""
        if not codigo_restaurante.value.strip():
            aviso.value = "Digite o código do restaurante."
            page.update()
            return

        itens = carregar_itens()
        if itens is None:
            page.update()
            return
        if len(itens) == 0:
            aviso.value = "Nenhum item pendente no momento."
            page.update()
            return

        # Montar interface principal
        page.controls.clear()
        page.add(
            ft.Text("Painel da Cozinha", size=30, weight="bold"),
            aviso,
            itens_container,
            ft.ElevatedButton("Atualizar", on_click=atualizar_lista),
        )
        atualizar_lista()



    confirmar_btn = ft.ElevatedButton("Entrar", on_click=confirmar_codigo)


    page.add(
        ft.Text("Painel da Cozinha", size=30, weight="bold"),
        codigo_restaurante,
        confirmar_btn,
        aviso,
        itens_container
    )

ft.app(target=main)

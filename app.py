import flet as ft
import garcom
import caixa

def main(page: ft.Page):
    page.title = "Sistema de Restaurante"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 5
    page.window_width = 900
    page.window_height = 700
    page.bgcolor = ft.Colors.GREY_100
    page.viewport_scale = True
    page.web_head = """
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    """

    def route_change(route):
        page.controls.clear()
        if page.route == "/garcom":
            garcom.main(page)  # Chama a função main do garcom.py
        elif page.route == "/caixa":
            caixa.main(page)  # Chama a função main do caixa.py
        else:
            # Tela inicial para selecionar o módulo
            page.add(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Bem-vindo ao Sistema de Restaurante",
                                size=28,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLUE_900,
                            ),
                            ft.ElevatedButton(
                                "Acessar Sistema do Garçom",
                                on_click=lambda e: page.go("/garcom"),
                                bgcolor=ft.Colors.GREEN_400,
                                color=ft.Colors.WHITE,
                                width=300,
                                height=50,
                            ),
                            ft.ElevatedButton(
                                "Acessar Sistema do Caixa",
                                on_click=lambda e: page.go("/caixa"),
                                bgcolor=ft.Colors.BLUE_400,
                                color=ft.Colors.WHITE,
                                width=300,
                                height=50,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=20,
                    ),
                    alignment=ft.alignment.center,
                    expand=True,
                )
            )
        page.update()

    page.on_route_change = route_change
    page.go(page.route or "/")  # Inicia na tela inicial

ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=8500)
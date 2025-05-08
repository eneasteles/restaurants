
import flet as ft
 
if __name__ == "__main__":
 
    def main(page: ft.Page):
 
        page.title = "Flet Trello clone"
        page.padding = 0
        page.bgcolor = colors.BLUE_GREY_200
        app = TrelloApp(page)
        page.add(app)
        page.update()
 
    ft.app(main)

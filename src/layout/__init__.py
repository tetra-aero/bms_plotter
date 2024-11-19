import flet as ft


class Sheet(ft.Card):
    def __init__(self, title: str, filter_str: str, content: ft.GridView):
        super().__init__()
        self.title = title
        self.content: ft.GridView = content
        self.filter = filter_str
        self.card = self.build_card()

    def build_card(self) -> ft.Card:
        return ft.Card(
            ft.Container(
                content=ft.Column(
                    [
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.ACCESSIBILITY),
                            title=ft.Text(self.title),
                        ),
                        ft.Row([self.content]),
                    ]
                ),
                alignment=ft.alignment.center,
                border_radius=ft.border_radius.all(5),
            )
        )

    def update_content(self, name: str, new_content: ft.Control):
        if self.filter:
            if self.filter in name:
                self.content.controls.append(new_content)
                # self.update()

    def build(self):
        return self.card

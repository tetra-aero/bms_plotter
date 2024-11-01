import flet as ft


def Sheet(title: str, content: ft.Control) -> ft.Control:
    return ft.Card(
        ft.Container(
            content=ft.Column(
                [
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.ACCESSIBILITY),
                        title=ft.Text(title),
                    ),
                    ft.Row(
                        [content],
                    ),
                ]
            ),
            alignment=ft.alignment.center,
            border_radius=ft.border_radius.all(5),
        )
    )


def graphs() -> ft.Control:
    data_1 = [
        ft.LineChartData(
            data_points=[
                ft.LineChartDataPoint(1, 1),
                ft.LineChartDataPoint(3, 1.5),
                ft.LineChartDataPoint(5, 1.4),
                ft.LineChartDataPoint(7, 3.4),
                ft.LineChartDataPoint(10, 2),
                ft.LineChartDataPoint(12, 2.2),
                ft.LineChartDataPoint(13, 1.8),
            ],
            stroke_width=1,
            color=ft.colors.LIGHT_GREEN,
            curved=True,
            stroke_cap_round=True,
        ),
    ]

    graphs = ft.GridView(
        expand=1,
        runs_count=1,
        max_extent=300,
        child_aspect_ratio=1.0,
        spacing=5,
        run_spacing=5,
    )

    for i in range(0, 5):
        graphs.controls.append(
            ft.LineChart(
                data_series=data_1,
                border=ft.Border(
                    bottom=ft.BorderSide(
                        4, ft.colors.with_opacity(0.5, ft.colors.ON_SURFACE)
                    )
                ),
                left_axis=ft.ChartAxis(
                    labels=[
                        ft.ChartAxisLabel(
                            value=1,
                            label=ft.Text("1m", size=14, weight=ft.FontWeight.BOLD),
                        ),
                        ft.ChartAxisLabel(
                            value=2,
                            label=ft.Text("2m", size=14, weight=ft.FontWeight.BOLD),
                        ),
                        ft.ChartAxisLabel(
                            value=3,
                            label=ft.Text("3m", size=14, weight=ft.FontWeight.BOLD),
                        ),
                        ft.ChartAxisLabel(
                            value=4,
                            label=ft.Text("4m", size=14, weight=ft.FontWeight.BOLD),
                        ),
                        ft.ChartAxisLabel(
                            value=5,
                            label=ft.Text("5m", size=14, weight=ft.FontWeight.BOLD),
                        ),
                        ft.ChartAxisLabel(
                            value=6,
                            label=ft.Text("6m", size=14, weight=ft.FontWeight.BOLD),
                        ),
                    ],
                    labels_size=40,
                ),
                bottom_axis=ft.ChartAxis(
                    labels=[
                        ft.ChartAxisLabel(
                            value=2,
                            label=ft.Container(
                                ft.Text(
                                    "SEP",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.with_opacity(
                                        0.5, ft.colors.ON_SURFACE
                                    ),
                                ),
                                margin=ft.margin.only(top=10),
                            ),
                        ),
                        ft.ChartAxisLabel(
                            value=7,
                            label=ft.Container(
                                ft.Text(
                                    "OCT",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.with_opacity(
                                        0.5, ft.colors.ON_SURFACE
                                    ),
                                ),
                                margin=ft.margin.only(top=10),
                            ),
                        ),
                        ft.ChartAxisLabel(
                            value=12,
                            label=ft.Container(
                                ft.Text(
                                    "DEC",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.with_opacity(
                                        0.5, ft.colors.ON_SURFACE
                                    ),
                                ),
                                margin=ft.margin.only(top=10),
                            ),
                        ),
                    ],
                    labels_size=32,
                ),
                tooltip_bgcolor=ft.colors.with_opacity(0.8, ft.colors.BLUE_GREY),
                min_y=0,
                max_y=4,
                min_x=0,
                max_x=14,
                animate=5000,
                expand=True,
            )
        )

    return graphs


def main_page() -> ft.Control:
    items = []
    items.append(Sheet("Bus Current", graphs()))
    items.append(Sheet("Bus Voltage", graphs()))
    items.append(Sheet("Temperature", graphs()))
    items.append(Sheet("Cell Voltage", graphs()))
    return ft.Column(spacing=5, controls=items)


def main(page: ft.Page):
    page.title = "Tetra Battery Management System Plotter App"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 50
    page.update()

    page.add(main_page())

    page.update()


ft.app(main)

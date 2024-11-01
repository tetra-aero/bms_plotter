import flet as ft


def items(count):
    items = []
    items.append(
        ft.Card(
            ft.Container(
                content=ft.Stack([ft.Text("Temperature", size=30)]),
                alignment=ft.alignment.center,
                border_radius=ft.border_radius.all(5),
            )
        )
    )
    items.append(
        ft.Card(
            ft.Container(
                content=ft.Stack([ft.Text("Temperature", size=30)]),
                alignment=ft.alignment.center,
                border_radius=ft.border_radius.all(5),
            )
        )
    )
    items.append(
        ft.Card(
            ft.Container(
                content=ft.Stack([ft.Text("Temperature", size=30)]),
                alignment=ft.alignment.center,
                border_radius=ft.border_radius.all(5),
            )
        )
    )
    items.append(
        ft.Card(
            ft.Container(
                content=ft.Stack([ft.Text("Temperature", size=30)]),
                alignment=ft.alignment.center,
                border_radius=ft.border_radius.all(5),
            )
        )
    )
    return items


def main(page: ft.Page):
    page.title = "Tetra Battery Management System Plotter App"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 50
    page.update()

    graphs = ft.GridView(
        expand=1,
        runs_count=1,
        max_extent=300,
        child_aspect_ratio=1.0,
        spacing=5,
        run_spacing=5,
    )
    page.add(ft.Column(spacing=5, controls=items(5)))
    page.add(ft.Text("Temperature", size=30))
    page.add(ft.Text("Bus Current", size=30))
    page.add(ft.Text("Bus Voltage", size=30))
    page.add(ft.Text("Cell Voltage", size=30))

    page.add(graphs)
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
            stroke_width=8,
            color=ft.colors.LIGHT_GREEN,
            curved=True,
            stroke_cap_round=True,
        ),
        ft.LineChartData(
            data_points=[
                ft.LineChartDataPoint(1, 1),
                ft.LineChartDataPoint(3, 2.8),
                ft.LineChartDataPoint(7, 1.2),
                ft.LineChartDataPoint(10, 2.8),
                ft.LineChartDataPoint(12, 2.6),
                ft.LineChartDataPoint(13, 3.9),
            ],
            color=ft.colors.PINK,
            below_line_bgcolor=ft.colors.with_opacity(0, ft.colors.PINK),
            stroke_width=8,
            curved=True,
            stroke_cap_round=True,
        ),
        ft.LineChartData(
            data_points=[
                ft.LineChartDataPoint(1, 2.8),
                ft.LineChartDataPoint(3, 1.9),
                ft.LineChartDataPoint(6, 3),
                ft.LineChartDataPoint(10, 1.3),
                ft.LineChartDataPoint(13, 2.5),
            ],
            color=ft.colors.CYAN,
            stroke_width=8,
            curved=True,
            stroke_cap_round=True,
        ),
    ]

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
    page.update()


ft.app(main)

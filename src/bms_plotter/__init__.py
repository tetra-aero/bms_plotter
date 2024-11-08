import threading
import time
from typing import Dict, List

import flet as ft

import can_utils as cu
import layout

line_charts: Dict[str, ft.LineChart] = {}
items: List[layout.Sheet] = []


def create_chart(title: str) -> ft.Control:
    chart = ft.LineChart(
        data_series=[],
        border=ft.Border(
            bottom=ft.BorderSide(4, ft.colors.with_opacity(0.5, ft.colors.ON_SURFACE))
        ),
        left_axis=ft.ChartAxis(
            labels_size=40,
        ),
        bottom_axis=ft.ChartAxis(
            labels_size=40,
        ),
        tooltip_bgcolor=ft.colors.with_opacity(0.8, ft.colors.RED_ACCENT),
        min_y=100.0,
        max_y=100.0,
        min_x=0,
        max_x=1000,
        animate=0,
        expand=True,
    )
    line_charts[title] = chart
    return ft.Column(
        controls=[
            ft.Text(value=title, size=24, weight="bold"),
            chart,
        ]
    )


def graphs(chart_keys: List[str]) -> ft.Control:
    global line_charts
    if "line_charts" not in globals():
        line_charts = {}
    for key in chart_keys:
        if key not in line_charts:
            create_chart(key)
    graphs = ft.GridView(
        expand=1,
        runs_count=1,
        max_extent=300,
        child_aspect_ratio=1.0,
        spacing=10,
        run_spacing=10,
    )
    for key in chart_keys:
        graphs.controls.append(line_charts[key])
    return graphs


def main_page() -> ft.Control:
    items.append(
        layout.Sheet(
            "Bus Current & Voltage & SoC",
            None,
            graphs(
                [
                    cu.CANParser.KEY_BATTERY_CURRENT,
                    cu.CANParser.KEY_BATTERY_VOLTAGE,
                    cu.CANParser.KEY_SOC,
                ]
            ),
        )
    )
    items.append(
        layout.Sheet(
            "Thurmista Temperature",
            None,
            graphs(
                [
                    cu.CANParser.KEY_BATTERY_AVERAGE_TEMP,
                    cu.CANParser.KEY_BATTERY_MAX_TEMP,
                    cu.CANParser.KEY_PCB_AVERAGE_TEMP,
                    cu.CANParser.KEY_PCB_MAX_TEMP,
                ]
            ),
        )
    )
    items.append(
        layout.Sheet(
            "Cell Voltage",
            cu.CANParser.KEY_CELL,
            graphs([]),
        )
    )
    return ft.Column(spacing=5, controls=items)


def main(page: ft.Page):
    page.title = "Tetra Battery Management System Plotter App"
    page.theme_mode = ft.ThemeMode.DARK
    # page.scroll = ft.ScrollMode.AUTO
    # page.window.frameless = True
    # page.window.full_screen = True
    # page.add(main_page())
    # page.update()

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        extended=True,
        min_width=100,
        min_extended_width=200,
        # leading=ft.FloatingActionButton(icon=ft.icons.CREATE, text="Add"),
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.icons.FAVORITE_BORDER,
                selected_icon=ft.icons.FAVORITE,
                label="General",
            ),
            ft.NavigationRailDestination(
                icon_content=ft.Icon(ft.icons.BOOKMARK_BORDER),
                selected_icon_content=ft.Icon(ft.icons.BOOKMARK),
                label="Detail",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.SETTINGS_OUTLINED,
                selected_icon_content=ft.Icon(ft.icons.SETTINGS),
                label_content=ft.Text("Setting"),
            ),
        ],
        on_change=lambda e: print("Selected destination:", e.control.selected_index),
    )
    main = main_page()
    # main.page.auto_scroll = ft.ScrollMode.AUTO
    # main.page.expand = True
    main.expand = True
    # main.

    page.add(
        ft.Row(
            [
                rail,
                ft.VerticalDivider(width=10),
                ft.GridView(
                    [main],
                    # alignment=ft.MainAxisAlignment.START,
                    expand=True,
                    # auto_scroll=True,
                ),
            ],
            expand=True,
        )
    )

    start_time = time.time()

    can_receiver = cu.CANReceiver()
    can_receiver.start_receiving()

    def update_chart():
        current_time = time.time() - start_time
        data_points = can_receiver.get_data_points()
        for key, data in data_points.items():
            if key in line_charts:
                if not line_charts[key].data_series:
                    line_charts[key].data_series.append(
                        ft.LineChartData(data_points=[])
                    )
                line_charts[key].data_series[0].data_points.append(
                    ft.LineChartDataPoint(data[-1][0] - start_time, data[-1][1])
                )
                line_charts[key].min_x = 0
                line_charts[key].max_x = current_time
                values = [point[1] for point in data]
                line_charts[key].min_y = min(values) - 1
                line_charts[key].max_y = max(values) * 1.1
            else:
                create_chart(key)
                for item in items:
                    item.update_content(key, line_charts[key])
        page.update()

    def update_task():
        while True:
            update_chart()
            time.sleep(0.5)

    update_thread = threading.Thread(target=update_task, daemon=True)
    update_thread.start()


ft.app(main)

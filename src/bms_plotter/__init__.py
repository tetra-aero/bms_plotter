import flet as ft
import can_utils as cu
import time
import threading

line_charts = []


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


def create_chart() -> ft.LineChart:
    return ft.LineChart(
        data_series=[ft.LineChartData(data_points=[ft.LineChartDataPoint(0, 0)])],
        border=ft.Border(
            bottom=ft.BorderSide(4, ft.colors.with_opacity(0.5, ft.colors.ON_SURFACE))
        ),
        left_axis=ft.ChartAxis(
            labels_size=40,
        ),
        bottom_axis=ft.ChartAxis(
            labels_size=32,
        ),
        tooltip_bgcolor=ft.colors.with_opacity(0.8, ft.colors.BLUE_GREY),
        min_y=-1.0,
        max_y=1.0,
        min_x=0,
        max_x=1000,
        animate=0,
        expand=True,
    )


def graphs() -> ft.Control:
    global line_charts
    line_charts = [create_chart() for _ in range(1)]  # Create multiple charts

    graphs = ft.GridView(
        expand=1,
        runs_count=1,
        max_extent=600,
        child_aspect_ratio=1.0,
        spacing=5,
        run_spacing=5,
    )

    for chart in line_charts:
        graphs.controls.append(chart)

    return graphs


def main_page() -> ft.Control:
    items = []
    items.append(Sheet("Bus Current", graphs()))
    return ft.Column(spacing=5, controls=items)


def main(page: ft.Page):
    page.title = "Tetra Battery Management System Plotter App"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 50

    can_receiver = cu.CANReceiver()
    can_receiver.start_receiving()
    page.add(main_page())
    page.update()

    def update_chart():
        current_time = time.time()
        data_points = can_receiver.get_data_points()
        battery_current_data = data_points["battery_current"]
        print(battery_current_data)

        for i, chart in enumerate(line_charts):
            chart.data_series[0].data_points = [
                ft.LineChartDataPoint(current_time + j, battery_current_data[j])
                for j in range(len(battery_current_data))
            ]

            chart.min_x = current_time
            chart.max_x = current_time + len(battery_current_data)
        page.update()

    def update_task():
        while True:
            update_chart()
            time.sleep(1.0)

    update_thread = threading.Thread(target=update_task, daemon=True)
    update_thread.start()


ft.app(main)

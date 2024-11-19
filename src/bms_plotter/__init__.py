import csv
import datetime
import os
import threading
import time
from typing import Dict, List, Optional

import flet as ft

import can_utils as cu
import layout

line_charts: Dict[str, ft.LineChart] = {}
items_mainpage: List[layout.Sheet] = []
items_setting: List[layout.Sheet] = []
items_general: List[layout.Sheet] = []
last_written_timestamp = None
filename = ""
lock_listen = threading.Lock()
device_id = 0x01
bus_name = "can0"
bus_baudrate = 500000
can_receiver: Optional[cu.CANReceiver] = None


def start_listen(e):
    if not lock_listen.locked():
        lock_listen.acquire()
        global can_receiver
        can_receiver = cu.CANReceiver(
            channel=bus_name, bitrate=bus_baudrate, bms_id=device_id
        )
        can_receiver.start_receiving()


def stop_listen(e):
    if lock_listen.locked():
        global can_receiver
        can_receiver.stop_receiving()
        lock_listen.release()


def handle_bus_name(e):
    global bus_name
    bus_name = e.control.value


def handle_bus_baudrate(e):
    global bus_baudrate
    bus_baudrate = int(e.control.value)


def handle_device_id(e):
    global device_id
    device_id = int(e.control.value)


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
    for key in chart_keys:
        if key not in line_charts:
            create_chart(key)
    graphs = ft.GridView(
        auto_scroll=True,
        runs_count=1,
        max_extent=300,
        child_aspect_ratio=1.0,
        spacing=10,
        run_spacing=10,
    )
    for key in chart_keys:
        graphs.controls.append(line_charts[key])
    return graphs


def detail_page() -> ft.Control:
    items_mainpage.append(
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
    items_mainpage.append(
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
    items_mainpage.append(
        layout.Sheet(
            "Cell Voltage",
            cu.CANParser.KEY_CELL,
            graphs([]),
        )
    )
    return ft.Column(
        spacing=5,
        controls=items_mainpage,
        expand=True,
        scroll=True,
    )


def handle_chart_visibility(e):
    key = e.control.label
    if key in line_charts:
        line_charts[key].visible = e.control.value


def setting_page() -> ft.Control:
    # items_setting.append()
    return ft.Column(
        spacing=5,
        expand=True,
        scroll=True,
        controls=[
            ft.TextField(
                label="CAN bus Name",
                value=bus_name,
                autofill_hints=ft.AutofillHint.NAME,
                on_change=handle_bus_name,
            ),
            ft.TextField(
                label="Can bus Baudrate",
                value=bus_baudrate,
                autofill_hints=ft.AutofillHint.NAME,
                on_change=handle_bus_baudrate,
            ),
            ft.TextField(
                label="BMS Can Device ID (decimal)",
                value=device_id,
                autofill_hints=ft.AutofillHint.NAME,
                on_change=handle_device_id,
            ),
            ft.ExpansionTile(
                title=ft.Text("General"),
                initially_expanded=True,
                collapsed_text_color=ft.colors.BLUE,
                text_color=ft.colors.BLUE,
                controls=[
                    *[
                        ft.Checkbox(
                            label=key,
                            value=True,
                            on_change=handle_chart_visibility,
                        )
                        for key in line_charts.keys()
                    ]
                ],
            ),
            ft.ExpansionTile(
                title=ft.Text("Cell Series"),
                initially_expanded=True,
                collapsed_text_color=ft.colors.BLUE,
                text_color=ft.colors.BLUE,
                controls=[
                    *[
                        ft.Checkbox(
                            label=key,
                            value=True,
                            on_change=handle_chart_visibility,
                        )
                        for key in line_charts.keys()
                    ]
                ],
            ),
            ft.ExpansionTile(
                title=ft.Text("Temp Series"),
                initially_expanded=True,
                collapsed_text_color=ft.colors.BLUE,
                text_color=ft.colors.BLUE,
                controls=[
                    *[
                        ft.Checkbox(
                            label=key,
                            value=True,
                            on_change=handle_chart_visibility,
                        )
                        for key in line_charts.keys()
                    ]
                ],
            ),
        ],
    )


def general_page() -> ft.Control:
    # items_general.append()
    return ft.Column(spacing=5, controls=items_general)


def main(page: ft.Page):
    page.title = "Tetra Battery Management System Plotter App"
    page.theme_mode = ft.ThemeMode.DARK
    start_time = time.time()

    content_detail = detail_page()
    content_general = general_page()
    content_setting = setting_page()

    main_container = ft.Container()
    main_container.content = content_general

    def callback_full_recharge(e: any):
        can_receiver.notice_full_recharge()

    def handle_page(e):
        page_num = e.control.selected_index
        if page_num == 0:
            main_container.content = content_general
        elif page_num == 1:
            main_container.content = content_detail
        elif page_num == 2:
            main_container.content = content_setting
        page.update()

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        extended=True,
        min_width=100,
        min_extended_width=100,
        group_alignment=-1.0,
        on_change=handle_page,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.icons.AUTO_GRAPH,
                selected_icon=ft.Icon(ft.icons.AUTO_GRAPH),
                label="General",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.SPACE_DASHBOARD_OUTLINED,
                selected_icon=ft.Icon(ft.icons.SPACE_DASHBOARD),
                label="Detail",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.SETTINGS_OUTLINED,
                selected_icon_content=ft.Icon(ft.icons.SETTINGS),
                label_content=ft.Text("Setting"),
            ),
        ],
    )

    page.add(
        ft.Column(
            [
                ft.Row(
                    [
                        rail,
                        ft.VerticalDivider(width=10),
                        ft.Container(
                            content=main_container,
                            expand=True,
                            alignment=ft.alignment.top_left,
                        ),
                    ],
                    expand=True,
                ),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.OutlinedButton(
                                "Notify FULL",
                                icon="battery_charging_full",
                                icon_color="yellow400",
                                on_click=callback_full_recharge,
                            ),
                            ft.OutlinedButton(
                                "Start Listening",
                                icon=ft.icons.NOT_STARTED,
                                icon_color="green400",
                                on_click=start_listen,
                            ),
                            ft.OutlinedButton(
                                "Stop Listening",
                                icon=ft.icons.STOP_CIRCLE_ROUNDED,
                                icon_color="red400",
                                on_click=stop_listen,
                            ),
                            ft.OutlinedButton(
                                "Next CSV",
                                icon=ft.icons.NAVIGATE_NEXT,
                                icon_color="green400",
                                on_click=stop_listen,
                            ),
                            ft.OutlinedButton(
                                "Clear Data",
                                icon=ft.icons.CLEAR_OUTLINED,
                                icon_color="red400",
                                on_click=stop_listen,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    expand=False,
                    alignment=ft.alignment.bottom_left,
                ),
            ],
            expand=True,
        )
    )

    def update_chart():
        current_time = time.time() - start_time
        global can_receiver
        if can_receiver is not None:
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
                    for item in items_mainpage:
                        item.update_content(key, line_charts[key])
        page.update()

    def update_csv():
        global last_written_timestamp
        current_date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
        file_name = f"{current_date}.csv"
        if can_receiver is not None:
            data_points = can_receiver.get_data_points()
            all_timestamps = set()
            for data in data_points.values():
                for timestamp, _ in data:
                    if (
                        last_written_timestamp is None
                        or timestamp > last_written_timestamp
                    ):
                        all_timestamps.add(timestamp)
            all_timestamps = sorted(all_timestamps)
            if not all_timestamps:
                return
            file_exists = os.path.exists(file_name)
            if not file_exists:
                with open(file_name, mode="w", newline="") as csv_file:
                    headers = ["timestamp"] + list(data_points.keys())
                    csv_writer = csv.writer(csv_file)
                    csv_writer.writerow(headers)
            with open(file_name, mode="a", newline="") as csv_file:
                csv_writer = csv.writer(csv_file)
                for timestamp in all_timestamps:
                    row = [timestamp]
                    for key in data_points.keys():
                        value = next(
                            (v for t, v in data_points[key] if t == timestamp), ""
                        )
                        row.append(value)
                    csv_writer.writerow(row)
            last_written_timestamp = max(all_timestamps)

    def update_task():
        while True:
            update_chart()
            update_csv()
            time.sleep(0.5)

    update_thread = threading.Thread(target=update_task, daemon=True)
    update_thread.start()


ft.app(main)

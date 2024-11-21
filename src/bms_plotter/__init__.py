import asyncio
import csv
import datetime
import os
from typing import Dict, List, Optional

import flet as ft

import can_utils as cu
import layout


class BatteryManagementApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.line_charts: Dict[str, ft.LineChart] = {}
        self.items_mainpage: List[layout.Sheet] = []
        self.can_receiver: Optional[cu.CANReceiver] = None

        self.bus_name = "can0"
        self.bus_baudrate = 500000
        self.device_id = 0x01
        self.last_written_timestamp = None

        self.start_time = datetime.datetime.now().timestamp()
        self.init_ui()

    def init_ui(self):
        self.page.title = "Tetra Battery Management System Plotter App"
        self.page.theme_mode = ft.ThemeMode.DARK

        self.main_container = ft.Container()
        self.content_detail = self.create_detail_page()
        self.content_general = self.create_general_page()
        self.content_setting = self.create_setting_page()

        self.main_container.content = self.content_general

        self.navigation_rail = self.create_navigation_rail()
        self.control_panel = self.create_control_panel()

        self.page.add(
            ft.Column(
                [
                    ft.Row(
                        [
                            self.navigation_rail,
                            ft.VerticalDivider(width=10),
                            ft.Container(
                                content=self.main_container,
                                expand=True,
                                alignment=ft.alignment.top_left,
                            ),
                        ],
                        expand=True,
                    ),
                    self.control_panel,
                ],
                expand=True,
            )
        )

    def create_navigation_rail(self) -> ft.NavigationRail:
        return ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            extended=True,
            min_width=100,
            min_extended_width=100,
            group_alignment=-1.0,
            on_change=self.handle_navigation,
            destinations=[
                ft.NavigationRailDestination(icon=ft.icons.AUTO_GRAPH, label="General"),
                ft.NavigationRailDestination(
                    icon=ft.icons.SPACE_DASHBOARD_OUTLINED, label="Detail"
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.SETTINGS_OUTLINED, label="Setting"
                ),
            ],
        )

    def create_control_panel(self) -> ft.Container:
        return ft.Container(
            content=ft.Row(
                [
                    ft.OutlinedButton(
                        "Notify FULL",
                        icon="battery_charging_full",
                        icon_color="yellow400",
                        on_click=self.callback_full_recharge,
                    ),
                    ft.OutlinedButton(
                        "Start Listening",
                        icon=ft.icons.NOT_STARTED,
                        icon_color="green400",
                        on_click=self.start_listen,
                    ),
                    ft.OutlinedButton(
                        "Stop Listening",
                        icon=ft.icons.STOP_CIRCLE_ROUNDED,
                        icon_color="red400",
                        on_click=self.stop_listen,
                    ),
                    ft.OutlinedButton(
                        "Next CSV",
                        icon=ft.icons.NAVIGATE_NEXT,
                        icon_color="green400",
                        on_click=self.save_next_csv,
                    ),
                    ft.OutlinedButton(
                        "Clear Data",
                        icon=ft.icons.CLEAR_OUTLINED,
                        icon_color="red400",
                        on_click=self.clear_data,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            expand=False,
            alignment=ft.alignment.bottom_left,
        )

    async def update_task(self):
        while True:
            await self.update_chart()
            await self.update_csv()
            await asyncio.sleep(1.0)

    def create_detail_page(self) -> ft.Control:
        self.items_mainpage.append(
            layout.Sheet(
                "Bus Current & Voltage & SoC",
                None,
                self.create_graphs(
                    [
                        cu.CANParser.KEY_BATTERY_CURRENT,
                        cu.CANParser.KEY_BATTERY_VOLTAGE,
                        cu.CANParser.KEY_SOC,
                    ]
                ),
            )
        )
        self.items_mainpage.append(
            layout.Sheet(
                "Thurmista Temperature",
                None,
                self.create_graphs(
                    [
                        cu.CANParser.KEY_BATTERY_AVERAGE_TEMP,
                        cu.CANParser.KEY_BATTERY_MAX_TEMP,
                        cu.CANParser.KEY_PCB_AVERAGE_TEMP,
                        cu.CANParser.KEY_PCB_MAX_TEMP,
                    ]
                ),
            )
        )
        self.items_mainpage.append(
            layout.Sheet("Cell Voltage", cu.CANParser.KEY_CELL, self.create_graphs([]))
        )
        return ft.Column(
            spacing=5,
            controls=self.items_mainpage,
            expand=True,
            scroll=True,
        )

    def create_general_page(self) -> ft.Control:
        return ft.Column(spacing=5, controls=[])

    def handle_chart_visibility(self, e: ft.ControlEvent, key: str):
        if key in self.line_charts:
            self.line_charts[key].visible = e.control.value
            # self.page.update()

    def create_setting_page(self) -> ft.Control:
        return ft.Column(
            spacing=5,
            expand=True,
            scroll=True,
            controls=[
                ft.TextField(
                    label="CAN bus Name",
                    value=self.bus_name,
                    on_change=lambda e: setattr(self, "bus_name", e.control.value),
                ),
                ft.TextField(
                    label="CAN bus Baudrate",
                    value=str(self.bus_baudrate),
                    on_change=lambda e: setattr(
                        self, "bus_baudrate", int(e.control.value)
                    ),
                ),
                ft.TextField(
                    label="BMS Can Device ID (decimal)",
                    value=str(self.device_id),
                    on_change=lambda e: setattr(
                        self, "device_id", int(e.control.value)
                    ),
                ),
                ft.ExpansionTile(
                    title=ft.Text("Temp Series"),
                    initially_expanded=True,
                    collapsed_text_color=ft.colors.BLUE,
                    text_color=ft.colors.BLUE,
                    controls=[
                        ft.Column(
                            [
                                ft.Checkbox(
                                    label=key,
                                    value=self.line_charts[key].visible
                                    if key in self.line_charts
                                    else True,
                                    on_change=lambda e,
                                    k=key: self.handle_chart_visibility(e, k),
                                )
                                for key in sorted(self.line_charts.keys())
                            ]
                        )
                    ],
                ),
            ],
        )

    def create_graphs(self, chart_keys: List[str]) -> ft.Control:
        controls = []
        for key in chart_keys:
            if key not in self.line_charts:
                self.line_charts[key] = self.create_chart(key)
            controls.append(self.line_charts[key])
        return ft.GridView(
            auto_scroll=True,
            runs_count=1,
            max_extent=300,
            child_aspect_ratio=1.0,
            spacing=10,
            run_spacing=10,
            controls=controls,
        )

    def create_chart(self, title: str) -> ft.LineChart:
        chart = ft.LineChart(
            data_series=[],
            border=ft.Border(
                bottom=ft.BorderSide(
                    4, ft.colors.with_opacity(0.5, ft.colors.ON_SURFACE)
                )
            ),
            left_axis=ft.ChartAxis(labels_size=40),
            bottom_axis=ft.ChartAxis(labels_size=40),
            tooltip_bgcolor=ft.colors.with_opacity(0.8, ft.colors.RED_ACCENT),
        )
        return chart

    def handle_navigation(self, e: ft.ControlEvent):
        page_num = e.control.selected_index
        if page_num == 0:
            self.main_container.content = self.content_general
        elif page_num == 1:
            self.main_container.content = self.content_detail
        elif page_num == 2:
            self.main_container.content = self.content_setting
        self.page.update()

    def callback_full_recharge(self, e: ft.ControlEvent):
        if self.can_receiver:
            self.can_receiver.notice_full_recharge()

    def start_listen(self, e: ft.ControlEvent):
        self.start_time = datetime.datetime.now().timestamp()
        if not self.can_receiver:
            self.can_receiver = cu.CANReceiver(
                channel=self.bus_name,
                bitrate=self.bus_baudrate,
                bms_id=self.device_id,
            )
            self.can_receiver.start_receiving()
            asyncio.run(self.can_receiver.process_messages())

    def stop_listen(self, e: ft.ControlEvent):
        if self.can_receiver:
            self.can_receiver.stop_receiving()
            self.can_receiver = None

    async def update_chart(self):
        if not self.can_receiver:
            return

        current_time = datetime.datetime.now().timestamp() - self.start_time
        data_points = await self.can_receiver.get_data_points()

        if not data_points:
            return

        for key, data in data_points.items():
            if key in self.line_charts:
                if not self.line_charts[key].data_series:
                    self.line_charts[key].data_series.append(
                        ft.LineChartData(data_points=[])
                    )
                self.line_charts[key].data_series[0].data_points.append(
                    ft.LineChartDataPoint(x=current_time, y=data[-1][1])
                )
                self.line_charts[key].min_x = 0
                self.line_charts[key].max_x = current_time
                values = [point[1] for point in data]
                self.line_charts[key].min_y = min(values) - 1
                self.line_charts[key].max_y = max(values) * 1.1
            else:
                self.line_charts[key] = self.create_chart(key)

                for item in self.items_mainpage:
                    item.update_content(key, self.line_charts[key])

        self.page.update()

    async def update_csv(self):
        if not self.can_receiver:
            return

        current_date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
        file_name = f"{current_date}.csv"

        data_points = await self.can_receiver.get_data_points()
        if not data_points:
            return
        all_timestamps = sorted(
            {
                int(timestamp)
                for key_data in data_points.values()
                for timestamp, _ in key_data
                if self.last_written_timestamp is None
                or timestamp > self.last_written_timestamp
            }
        )

        if not all_timestamps:
            return
        file_exists = os.path.exists(file_name)
        if not file_exists:
            headers = ["timestamp"] + list(data_points.keys())
            with open(file_name, mode="w", newline="") as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(headers)

        with open(file_name, mode="a", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            for timestamp in all_timestamps:
                row = [timestamp]
                for key in data_points.keys():
                    value = next((v for t, v in data_points[key] if t == timestamp), "")
                    row.append(value)
                csv_writer.writerow(row)
        self.last_written_timestamp = max(all_timestamps)

    def save_next_csv(self, e: ft.ControlEvent):
        print(e)

    def clear_data(self, e: ft.ControlEvent):
        for chart in self.line_charts.values():
            if chart.data_series:
                chart.data_series.clear()
        self.start_time = datetime.datetime.now().timestamp()
        self.page.update()


def main(page: ft.Page):
    app = BatteryManagementApp(page)
    asyncio.run(app.update_task())


ft.app(main)

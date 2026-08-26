import flet as ft
from ui.theme import AppColors, button_hover_style

class TerminalWindow(object):
    def __init__(self, page: ft.Page, title: str = "Live Terminal Output"):
        self.page = page
        self.title = title
        self.output_list = ft.ListView(expand=True, spacing=2, auto_scroll=False)
        
        self.clear_btn = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINED,
            icon_color=AppColors.TEXT_MUTED,
            tooltip="Clear Terminal",
            icon_size=18,
            style=button_hover_style,
            on_click=self.clear
        )
        
        self.container = ft.Container(
            content=self.output_list,
            height=160,
            bgcolor=AppColors.TERMINAL_BG,
            border_radius=8,
            padding=10,
            border=ft.Border.all(1, AppColors.BORDER)
        )
        
        self.view = ft.Column([
            ft.Row([
                ft.Text(self.title, size=13, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED),
                self.clear_btn
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            self.container
        ], spacing=6)

    def get_control(self) -> ft.Control:
        return self.view

    def clear(self, e=None):
        self.output_list.controls.clear()
        self.output_list.controls.append(
            ft.Text("Terminal cleared.", color=ft.Colors.WHITE_54, italic=True, size=12)
        )
        if self.page:
            self.page.update()

    def append_line(self, line: str):
        if not line:
            return
        
        line_color = ft.Colors.GREEN_400
        if "[ERROR]" in line or "[FAIL]" in line or "Traceback" in line or "Exception" in line:
            line_color = ft.Colors.RED_400
        elif "[WARNING]" in line or "[WARN]" in line:
            line_color = ft.Colors.AMBER_400
        elif "[SKIPPED]" in line or "Skipped" in line:
            line_color = ft.Colors.CYAN_300
            
        self.output_list.controls.append(
            ft.Text(line, color=line_color, font_family="Consolas", selectable=True, size=12)
        )
        
        if len(self.output_list.controls) > 500:
            del self.output_list.controls[0]

    async def append_line_and_scroll(self, line: str):
        self.append_line(line)
        if self.page:
            self.page.update()
            await self.output_list.scroll_to(offset=-1, duration=30)

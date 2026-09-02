import flet as ft
from ui.theme import AppColors, button_hover_style

class TerminalWindow(object):
    def __init__(self, page: ft.Page, title: str = "Live Terminal Output"):
        self.page = page
        self.title = title
        self.output_list = ft.ListView(expand=True, spacing=2, auto_scroll=False)
        
        self.copy_btn = ft.IconButton(
            icon=ft.Icons.COPY_OUTLINED,
            icon_color=AppColors.TEXT_MUTED,
            tooltip="Copy Terminal Logs to Clipboard",
            icon_size=18,
            style=button_hover_style,
            on_click=self.copy_logs
        )

        self.clear_btn = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINED,
            icon_color=AppColors.TEXT_MUTED,
            tooltip="Clear Terminal",
            icon_size=18,
            style=button_hover_style,
            on_click=self.clear
        )
        
        self.container = ft.Container(
            content=ft.SelectionArea(content=self.output_list),
            height=180,
            bgcolor=AppColors.TERMINAL_BG,
            border_radius=8,
            padding=10,
            border=ft.Border.all(1, AppColors.BORDER)
        )
        
        self.view = ft.Column([
            ft.Row([
                ft.Text(self.title, size=13, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MUTED),
                ft.Row([self.copy_btn, self.clear_btn], spacing=4)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            self.container
        ], spacing=6)

    def get_control(self) -> ft.Control:
        return self.view

    def clear(self, e=None):
        self.output_list.controls.clear()
        self.output_list.controls.append(
            ft.Text("Terminal cleared.", color=ft.Colors.WHITE_54, italic=True, size=12, selectable=True)
        )
        if self.page:
            self.page.update()

    async def copy_logs(self, e=None):
        lines = []
        for ctrl in self.output_list.controls:
            if isinstance(ctrl, ft.Text) and ctrl.value:
                lines.append(ctrl.value)
        
        full_text = "\n".join(lines)
        if self.page and full_text:
            await ft.Clipboard().set(full_text)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("📋 Terminal logs copied to clipboard!"),
                bgcolor=ft.Colors.GREEN_800
            )
            self.page.snack_bar.open = True
            self.page.update()

    def append_line(self, line: str):
        if not line:
            return
        
        line_color = ft.Colors.GREEN_400
        if "[ERROR]" in line or "[FAIL]" in line or "Traceback" in line or "Exception" in line or "BrokenProcessPool" in line:
            line_color = ft.Colors.RED_400
        elif "[WARN]" in line or "[WARNING]" in line:
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

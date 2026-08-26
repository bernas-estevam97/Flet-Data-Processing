import flet as ft

class AppColors:
    PRIMARY = ft.Colors.CYAN_700
    ACCENT = ft.Colors.AMBER_600
    BG_CARD = ft.Colors.SURFACE_CONTAINER_HIGHEST
    TERMINAL_BG = ft.Colors.BLACK_87
    BORDER = ft.Colors.OUTLINE
    TEXT_MAIN = ft.Colors.ON_SURFACE
    TEXT_MUTED = ft.Colors.ON_SURFACE_VARIANT
    PATH_TEXT = ft.Colors.CYAN_700
    SUCCESS = ft.Colors.GREEN_700
    ERROR = ft.Colors.RED_700
    WARNING = ft.Colors.AMBER_700

# Reusable button style providing hand cursor on hover
button_hover_style = ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK)

def primary_button_style():
    return ft.ButtonStyle(
        mouse_cursor=ft.MouseCursor.CLICK,
        color=ft.Colors.WHITE,
        bgcolor=AppColors.PRIMARY
    )

def create_card(content: ft.Control, title: str = None, icon: str = None) -> ft.Container:
    controls = []
    if title:
        header_children = []
        if icon:
            header_children.append(ft.Icon(icon, color=AppColors.PRIMARY, size=20))
        header_children.append(ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN))
        controls.append(ft.Row(header_children, spacing=8))
        controls.append(ft.Divider(height=1, color=AppColors.BORDER))
    
    controls.append(content)
    
    return ft.Container(
        content=ft.Column(controls, spacing=12),
        padding=16,
        bgcolor=AppColors.BG_CARD,
        border_radius=10,
        border=ft.Border.all(1, AppColors.BORDER)
    )

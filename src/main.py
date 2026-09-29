import flet as ft
import sys
import os

# Add src directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import multiprocessing
from process_manager import process_manager
from ui.theme import AppColors, button_hover_style
from ui.views.tutorial_view import build_tutorial_view
from ui.views.filtering_view import build_filtering_view
from ui.views.stats_view import build_stats_view
from ui.views.stats_aio_view import build_stats_aio_view
from ui.views.merge_view import build_merge_view

def main(page: ft.Page):
    # App Window & Theme Configuration
    page.title = "Data Processing - MotoRater"
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.window_width = 1050
    page.window_height = 850
    page.padding = 0

    icon_ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.ico")
    icon_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.png")
    icon_path = icon_ico if os.path.exists(icon_ico) else icon_png
    if os.path.exists(icon_path):
        page.window.icon = icon_path
        if hasattr(page, "window_icon"):
            page.window_icon = icon_path

    # Build view instances
    tutorial_view = build_tutorial_view(page)
    filtering_view = build_filtering_view(page)
    stats_view = build_stats_view(page)
    stats_aio_view = build_stats_aio_view(page)
    merge_view = build_merge_view(page)

    main_content_area = ft.Container(
        content=tutorial_view,
        expand=True,
        padding=20
    )

    def on_nav_change(e):
        index = e.control.selected_index
        if index == 0:
            main_content_area.content = tutorial_view
        elif index == 1:
            main_content_area.content = filtering_view
        elif index == 2:
            main_content_area.content = stats_view
        elif index == 3:
            main_content_area.content = stats_aio_view
        elif index == 4:
            main_content_area.content = merge_view
        page.update()

    def create_nav_destination(icon_name, selected_icon_name, label_text):
        return ft.NavigationRailDestination(
            icon=ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK, 
                content=ft.Icon(icon_name)
            ),
            selected_icon=ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK, 
                content=ft.Icon(selected_icon_name)
            ),
            label=ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK, 
                content=ft.Text(label_text)
            )
        )

    sidebar = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        group_alignment=-0.9,
        destinations=[
            create_nav_destination(ft.Icons.HELP_OUTLINE, ft.Icons.HELP, "Tutorial"),
            create_nav_destination(ft.Icons.FILTER_ALT_OUTLINED, ft.Icons.FILTER_ALT, "Data Filtering"),
            create_nav_destination(ft.Icons.BAR_CHART_OUTLINED, ft.Icons.BAR_CHART, "Statistics"),
            create_nav_destination(ft.Icons.BAR_CHART_ROUNDED, ft.Icons.BAR_CHART, "Statistics - AIO"),
            create_nav_destination(ft.Icons.MERGE_TYPE_OUTLINED, ft.Icons.CALL_MERGE, "Merge Data"),
        ],
        on_change=on_nav_change,
        expand=True
    )

    is_system_dark = page.platform_brightness == ft.Brightness.DARK

    def toggle_theme(e):
        current_is_dark = page.theme_mode == ft.ThemeMode.DARK or (
            page.theme_mode == ft.ThemeMode.SYSTEM and page.platform_brightness == ft.Brightness.DARK
        )
        
        if current_is_dark:
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_icon_button.icon = ft.Icons.DARK_MODE
            theme_icon_button.tooltip = "Switch to Dark Mode"
        else:
            page.theme_mode = ft.ThemeMode.DARK
            theme_icon_button.icon = ft.Icons.LIGHT_MODE
            theme_icon_button.tooltip = "Switch to Light Mode"
            
        page.update()

    theme_icon_button = ft.IconButton(
        icon=ft.Icons.LIGHT_MODE if is_system_dark else ft.Icons.DARK_MODE,
        on_click=toggle_theme,
        style=button_hover_style,
        tooltip="Switch to Light Mode" if is_system_dark else "Switch to Dark Mode"
    )

    # Global Force Stop Controller
    global_stop_button = ft.IconButton(
        icon=ft.Icons.STOP_CIRCLE_OUTLINED,
        icon_color=AppColors.ERROR,
        icon_size=28,
        tooltip="No active processes",
        disabled=True,
        style=button_hover_style
    )
    running_badge = ft.Text("", size=11, color=AppColors.ERROR, weight=ft.FontWeight.BOLD, visible=False)

    def update_process_status():
        count = process_manager.get_running_count()
        if count > 0:
            names = process_manager.get_running_names()
            global_stop_button.disabled = False
            global_stop_button.icon = ft.Icons.STOP_CIRCLE
            global_stop_button.tooltip = f"Force Stop All Running Processes ({count} active: {', '.join(names)})"
            running_badge.value = f"{count} Active"
            running_badge.visible = True
        else:
            global_stop_button.disabled = True
            global_stop_button.icon = ft.Icons.STOP_CIRCLE_OUTLINED
            global_stop_button.tooltip = "No active processes"
            running_badge.value = ""
            running_badge.visible = False
        try:
            page.update()
        except Exception:
            pass

    async def on_force_stop_all(e):
        global_stop_button.disabled = True
        page.update()
        count = await process_manager.kill_all()
        if count > 0:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"⏹️ Force stopped {count} running process(es)."),
                bgcolor=ft.Colors.AMBER_800
            )
            page.snack_bar.open = True
            page.update()

    global_stop_button.on_click = on_force_stop_all
    process_manager.add_listener(update_process_status)

    def handle_window_event(e):
        if e.data == "close":
            process_manager.kill_all_sync()
            page.window.destroy()

    page.window.on_event = handle_window_event

    stop_control = ft.Column(
        [
            global_stop_button,
            running_badge
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=2
    )

    sidebar_layout = ft.Column(
        [
            sidebar, 
            ft.Container(content=stop_control, padding=ft.Padding.only(bottom=10)),
            ft.Container(content=theme_icon_button, padding=ft.Padding.only(bottom=20)) 
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

    page.add(
        ft.Row(
            [
                sidebar_layout,
                ft.VerticalDivider(width=1),
                main_content_area
            ],
            expand=True
        )
    )

if __name__ == "__main__":
    multiprocessing.freeze_support()
    ft.run(main)

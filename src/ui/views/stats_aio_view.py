import flet as ft
import asyncio
import sys
import os
import json
from ui.theme import AppColors, create_card, button_hover_style, primary_button_style
from ui.terminal import TerminalWindow

def build_stats_aio_view(page: ft.Page) -> ft.Control:
    status_text = ft.Text("System Ready", color=AppColors.TEXT_MUTED, size=14)

    input_folder_path = ""
    output_folder_path = ""

    selected_input_txt = ft.Text("No folder selected", color=AppColors.PATH_TEXT, italic=True, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)
    selected_output_txt = ft.Text("Defaults to input folder", color=AppColors.PATH_TEXT, italic=True, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)

    async def invoke_input_picker(e):
        nonlocal input_folder_path
        folder_path = await ft.FilePicker().get_directory_path(dialog_title="Select Filtered Data Folder")
        if folder_path:
            input_folder_path = folder_path
            selected_input_txt.value = folder_path
            page.update()

    async def invoke_output_picker(e):
        nonlocal output_folder_path
        folder_path = await ft.FilePicker().get_directory_path(dialog_title="Select Output Folder")
        if folder_path:
            output_folder_path = folder_path
            selected_output_txt.value = folder_path
            page.update()

    def reset_input_folder(e):
        nonlocal input_folder_path
        input_folder_path = ""
        selected_input_txt.value = "No folder selected"
        status_text.value = "Filtered data folder reset."
        status_text.color = AppColors.TEXT_MUTED
        page.update()

    def reset_output_folder(e):
        nonlocal output_folder_path
        output_folder_path = ""
        selected_output_txt.value = "Defaults to input folder"
        status_text.value = "Output folder reset."
        status_text.color = AppColors.TEXT_MUTED
        page.update()

    btn_select_input = ft.Button(
        "Select Filtered Folder",
        icon=ft.Icons.FOLDER_OPEN,
        style=button_hover_style,
        on_click=invoke_input_picker
    )

    btn_reset_input = ft.IconButton(
        icon=ft.Icons.RESTART_ALT,
        icon_color=AppColors.ERROR,
        tooltip="Reset Filtered Data Folder",
        style=button_hover_style,
        on_click=reset_input_folder
    )

    btn_select_output = ft.Button(
        "Select Output Folder",
        icon=ft.Icons.CREATE_NEW_FOLDER,
        style=button_hover_style,
        on_click=invoke_output_picker
    )

    btn_reset_output = ft.IconButton(
        icon=ft.Icons.RESTART_ALT,
        icon_color=AppColors.ERROR,
        tooltip="Reset Output Folder",
        style=button_hover_style,
        on_click=reset_output_folder
    )

    active_file_tags = {}
    tags_list_column = ft.Column(spacing=5)
    
    tags_list_container = ft.Container(
        content=tags_list_column,
        padding=10,
        bgcolor=ft.Colors.BLACK_12,
        border_radius=5,
        border=ft.Border.all(1, AppColors.BORDER),
        visible=False
    )

    tag_code_input = ft.TextField(label="File Tag (e.g., F)", width=150)
    tag_meaning_input = ft.TextField(label="Meaning (e.g., Female)", width=280)

    def remove_tag(code, row_control):
        if code in active_file_tags:
            del active_file_tags[code]
        tags_list_column.controls.remove(row_control)
        if not tags_list_column.controls:
            tags_list_container.visible = False
        page.update()

    def reset_all_tags(e):
        active_file_tags.clear()
        tags_list_column.controls.clear()
        tags_list_container.visible = False
        tag_code_input.value = ""
        tag_meaning_input.value = ""
        status_text.value = "All tags cleared."
        status_text.color = AppColors.TEXT_MUTED
        page.update()

    def add_tag(e):
        code = tag_code_input.value.strip().upper()
        meaning = tag_meaning_input.value.strip()

        if not code or not meaning:
            return
        if code in active_file_tags:
            return

        active_file_tags[code] = meaning
        tags_list_container.visible = True

        row_control = ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        row_control.controls = [
            ft.Text(f"🏷️  {code} ➔ {meaning}", color=AppColors.PRIMARY, weight=ft.FontWeight.BOLD, size=13),
            ft.IconButton(
                icon=ft.Icons.DELETE,
                icon_color=AppColors.ERROR,
                icon_size=18,
                style=button_hover_style,
                tooltip=f"Remove tag '{code}'",
                on_click=lambda _: remove_tag(code, row_control)
            )
        ]
        tags_list_column.controls.append(row_control)
        tag_code_input.value = ""
        tag_meaning_input.value = ""
        page.update()

    add_tag_btn = ft.Button("Add Tag", icon=ft.Icons.ADD, style=button_hover_style, on_click=add_tag)
    
    reset_tags_btn = ft.IconButton(
        icon=ft.Icons.CLEAR_ALL,
        icon_color=AppColors.ERROR,
        tooltip="Clear All Defined Tags",
        style=button_hover_style,
        on_click=reset_all_tags
    )

    group_trials_switch = ft.Switch(
        label="Group Trials by Base ID & Tags (Calculate Means)",
        value=True,
        active_color=AppColors.PRIMARY,
        tooltip="Averages trial files sharing base subject ID and identified tags"
    )

    terminal = TerminalWindow(page)
    progress_bar = ft.ProgressBar(visible=False, color=AppColors.PRIMARY)
    run_btn = ft.Button("Run Descriptive AIO Statistics", icon=ft.Icons.AUTO_AWESOME, style=primary_button_style())

    async def run_stats_aio(e):
        if not input_folder_path:
            status_text.value = "Please select a filtered data folder first!"
            status_text.color = AppColors.ERROR
            page.update()
            return

        out_path = output_folder_path if output_folder_path else input_folder_path
        tags_json_string = json.dumps(active_file_tags)
        should_group = "y" if group_trials_switch.value else "n"

        status_text.value = "Generating AIO statistics..."
        status_text.color = AppColors.WARNING
        
        terminal.clear()
        terminal.append_line("Starting descriptive statistics AIO script...")
        
        run_btn.disabled = True
        progress_bar.visible = True
        page.update()

        try:
            command = [
                sys.executable, "-u", os.path.join("src", "desc_analysis_aio.py"), 
                input_folder_path, out_path, "Tagged_Experiment", tags_json_string, should_group
            ]
            
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )

            line_count = 0
            while True:
                line = await process.stdout.readline()
                if not line:
                    break 
                
                decoded_line = line.decode('utf-8', errors='replace').strip()
                if decoded_line:
                    line_count += 1
                    terminal.append_line(decoded_line)
                    if line_count % 5 == 0:
                        page.update()

            await process.wait()

            if process.returncode == 0:
                status_text.value = "AIO Descriptive statistics completed successfully!"
                status_text.color = AppColors.SUCCESS
                page.snack_bar = ft.SnackBar(content=ft.Text("✅ Tagged AIO Statistics completed!"), bgcolor=ft.Colors.GREEN_800)
                page.snack_bar.open = True
            else:
                status_text.value = f"Script failed with exit code {process.returncode}"
                status_text.color = AppColors.ERROR

        except Exception as err:
            status_text.value = f"Error: {err}"
            status_text.color = AppColors.ERROR
            terminal.append_line(f"[ERROR] {err}")
            
        finally:
            run_btn.disabled = False
            progress_bar.visible = False
            page.update()

    run_btn.on_click = run_stats_aio

    folder_card = create_card(
        ft.Column([
            ft.Row([btn_select_input, btn_reset_input, selected_input_txt], alignment=ft.MainAxisAlignment.START, spacing=10),
            ft.Row([btn_select_output, btn_reset_output, selected_output_txt], alignment=ft.MainAxisAlignment.START, spacing=10),
        ], spacing=10),
        title="Directory Configuration",
        icon=ft.Icons.FOLDER
    )

    tagging_card = create_card(
        ft.Column([
            ft.Row([tag_code_input, tag_meaning_input, add_tag_btn, reset_tags_btn], spacing=10),
            tags_list_container,
            ft.Row([group_trials_switch], spacing=15),
        ], spacing=15),
        title="Dynamic File Tagging & Grouping",
        icon=ft.Icons.LABEL
    )

    return ft.ListView([
        ft.Text("Descriptive Statistics - All In One", size=22, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN),
        status_text,
        ft.Container(height=10),
        folder_card,
        tagging_card,
        run_btn,
        progress_bar,
        terminal.get_control()
    ], spacing=15, padding=20)

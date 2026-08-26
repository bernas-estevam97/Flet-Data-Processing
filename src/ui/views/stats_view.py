import flet as ft
import asyncio
import sys
import os
from ui.theme import AppColors, create_card, button_hover_style, primary_button_style
from ui.terminal import TerminalWindow

def build_stats_view(page: ft.Page) -> ft.Control:
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

    experiment_dropdown = ft.Dropdown(
        label="Experiment Type", value="footprint",
        options=[
            ft.dropdown.Option(key="footprint", text="Footprint"),
            ft.dropdown.Option(key="beam", text="Beam"),
            ft.dropdown.Option(key="swimming", text="Swimming"),
            ft.dropdown.Option(key="gridwalk", text="Gridwalk"),
        ], expand=True
    )

    group_trials_switch = ft.Switch(
        label="Group Trials by Base ID (Calculate Means)",
        value=True,
        active_color=AppColors.PRIMARY,
        tooltip="Averages trial files (_1, _2, etc.) sharing the same base subject ID"
    )

    terminal = TerminalWindow(page)
    progress_bar = ft.ProgressBar(visible=False, color=AppColors.PRIMARY)
    run_btn = ft.Button("Run Descriptive Statistics", icon=ft.Icons.ANALYTICS, style=primary_button_style())

    async def run_stats(e):
        if not input_folder_path:
            status_text.value = "Please select a filtered data folder first!"
            status_text.color = AppColors.ERROR
            page.update()
            return

        out_path = output_folder_path if output_folder_path else input_folder_path
        experiment = experiment_dropdown.value
        should_group = "y" if group_trials_switch.value else "n"

        status_text.value = "Generating statistics..."
        status_text.color = AppColors.WARNING
        
        terminal.clear()
        terminal.append_line("Starting descriptive statistics script...")
        
        run_btn.disabled = True
        progress_bar.visible = True
        page.update()

        try:
            command = [
                sys.executable, "-u", os.path.join("src", "desc_analysis.py"), 
                input_folder_path, out_path, experiment, should_group
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
                status_text.value = "Descriptive statistics generated successfully!"
                status_text.color = AppColors.SUCCESS
                page.snack_bar = ft.SnackBar(content=ft.Text("✅ Statistics compilation completed!"), bgcolor=ft.Colors.GREEN_800)
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

    run_btn.on_click = run_stats

    folder_card = create_card(
        ft.Column([
            ft.Row([btn_select_input, btn_reset_input, selected_input_txt], alignment=ft.MainAxisAlignment.START, spacing=10),
            ft.Row([btn_select_output, btn_reset_output, selected_output_txt], alignment=ft.MainAxisAlignment.START, spacing=10),
        ], spacing=10),
        title="Directory Configuration",
        icon=ft.Icons.FOLDER
    )

    params_card = create_card(
        ft.Column([
            ft.Row([experiment_dropdown], spacing=15),
            ft.Row([group_trials_switch], spacing=15),
        ], spacing=15),
        title="Analysis Configuration",
        icon=ft.Icons.SETTINGS
    )

    return ft.ListView([
        ft.Text("Descriptive Statistics", size=22, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN),
        status_text,
        ft.Container(height=10),
        folder_card,
        params_card,
        run_btn,
        progress_bar,
        terminal.get_control()
    ], spacing=15, padding=20)

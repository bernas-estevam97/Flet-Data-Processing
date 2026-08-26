import flet as ft
import asyncio
import sys
import os
from ui.theme import AppColors, create_card, button_hover_style, primary_button_style
from ui.terminal import TerminalWindow

def build_filtering_view(page: ft.Page) -> ft.Control:
    status_text = ft.Text("System Ready", color=AppColors.TEXT_MUTED, size=14)

    input_folder_path = ""
    output_folder_path = ""

    selected_input_txt = ft.Text("No folder selected", color=AppColors.PATH_TEXT, italic=True, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)
    selected_output_txt = ft.Text("Defaults to input folder", color=AppColors.PATH_TEXT, italic=True, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)

    async def invoke_input_picker(e):
        nonlocal input_folder_path
        folder_path = await ft.FilePicker().get_directory_path(dialog_title="Select Data Folder")
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
        status_text.value = "Data folder reset."
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
        "Select Data Folder",
        icon=ft.Icons.FOLDER_OPEN,
        style=button_hover_style,
        on_click=invoke_input_picker
    )

    btn_reset_input = ft.IconButton(
        icon=ft.Icons.RESTART_ALT,
        icon_color=AppColors.ERROR,
        tooltip="Reset Data Folder",
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

    cutoff_dropdown = ft.Dropdown(
        label="Cutoff Starts Where?", value="0",
        options=[
            ft.dropdown.Option(key="0", text="Tail Tip"),
            ft.dropdown.Option(key="1", text="Tail Center"),
            ft.dropdown.Option(key="2", text="Tail Base"),
            ft.dropdown.Option(key="3", text="Both Paws"),
        ], expand=True
    )

    animal_dropdown = ft.Dropdown(
        label="Animal Species", value="0",
        options=[
            ft.dropdown.Option(key="0", text="Mus Musculus"),
            ft.dropdown.Option(key="1", text="Acomys"),
        ], expand=True
    )

    experiment_dropdown = ft.Dropdown(
        label="Experiment Type", value="groundwalk",
        options=[
            ft.dropdown.Option(key="groundwalk", text="Groundwalk"),
            ft.dropdown.Option(key="gridwalk", text="Gridwalk"),
            ft.dropdown.Option(key="beamwalk", text="Beamwalk"),
            ft.dropdown.Option(key="swimming", text="Swimming"),
        ], expand=True
    )

    camera_dropdown = ft.Dropdown(
        label="Camera Settings", value="old",
        options=[
            ft.dropdown.Option(key="old", text="Old Settings"),
            ft.dropdown.Option(key="new", text="New Settings"),
        ], expand=True
    )

    height_cutoff_switch = ft.Switch(
        label="Apply Hind Paw Height Cutoff",
        value=False,
        active_color=AppColors.PRIMARY,
        tooltip="Truncate kinematics after hind paw threshold timestamp"
    )

    terminal = TerminalWindow(page)
    progress_bar = ft.ProgressBar(visible=False, color=AppColors.PRIMARY)
    run_btn = ft.Button("Run Data Filtering", icon=ft.Icons.PLAY_ARROW, style=primary_button_style())

    async def run_filtering(e):
        if not input_folder_path:
            status_text.value = "Please select a data folder first!"
            status_text.color = AppColors.ERROR
            page.update()
            return

        out_path = output_folder_path if output_folder_path else input_folder_path
        choice = cutoff_dropdown.value
        animal = animal_dropdown.value
        experiment = experiment_dropdown.value
        camera = camera_dropdown.value
        height_cutoff = "yes" if height_cutoff_switch.value else "no"

        status_text.value = "Processing... Please wait."
        status_text.color = AppColors.WARNING
        
        terminal.clear()
        terminal.append_line("Starting filtering script...")
        
        run_btn.disabled = True
        progress_bar.visible = True
        page.update()

        try:
            command = [
                sys.executable, "-u", os.path.join("src", "ex_filtering.py"), 
                input_folder_path, choice, animal, experiment, camera, out_path, height_cutoff
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
                status_text.value = "Filtering script executed successfully!"
                status_text.color = AppColors.SUCCESS
                page.snack_bar = ft.SnackBar(content=ft.Text("✅ Data filtering completed successfully!"), bgcolor=ft.Colors.GREEN_800)
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

    run_btn.on_click = run_filtering

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
            ft.Row([cutoff_dropdown, animal_dropdown], spacing=15),
            ft.Row([experiment_dropdown, camera_dropdown], spacing=15),
            ft.Row([height_cutoff_switch], spacing=15),
        ], spacing=15),
        title="Experiment Parameters",
        icon=ft.Icons.TUNE
    )

    return ft.ListView([
        ft.Text("Data Filtering", size=22, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN),
        status_text,
        ft.Container(height=10),
        folder_card,
        params_card,
        run_btn,
        progress_bar,
        terminal.get_control()
    ], spacing=15, padding=20)

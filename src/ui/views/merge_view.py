import flet as ft
import asyncio
import sys
import os
from ui.theme import AppColors, create_card, button_hover_style, primary_button_style
from ui.terminal import TerminalWindow

def build_merge_view(page: ft.Page) -> ft.Control:
    status_text = ft.Text("System Ready", color=AppColors.TEXT_MUTED, size=14)

    selected_files = []
    output_folder_path = ""

    selected_files_txt = ft.Text("No files selected", color=AppColors.PATH_TEXT, italic=True, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)
    selected_output_txt = ft.Text("No output folder selected", color=AppColors.PATH_TEXT, italic=True, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)

    output_filename_input = ft.TextField(label="Merged Output Filename", value="Merged_Data.xlsx")

    files_list_column = ft.Column(spacing=4)
    files_list_container = ft.Container(
        content=files_list_column,
        padding=10,
        bgcolor=ft.Colors.BLACK_12,
        border_radius=6,
        border=ft.Border.all(1, AppColors.BORDER),
        visible=False
    )

    def render_files_list():
        files_list_column.controls.clear()
        if not selected_files:
            files_list_container.visible = False
            selected_files_txt.value = "No files selected"
        else:
            files_list_container.visible = True
            selected_files_txt.value = f"{len(selected_files)} files selected"
            
            for path in selected_files:
                fname = os.path.basename(path)
                
                def make_remove_handler(file_p):
                    return lambda _: remove_single_file(file_p)

                row_control = ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.INSERT_DRIVE_FILE_OUTLINED, size=18, color=AppColors.PRIMARY),
                                ft.Text(fname, color=AppColors.TEXT_MAIN, size=13, weight=ft.FontWeight.W_500, overflow=ft.TextOverflow.ELLIPSIS),
                            ],
                            spacing=8,
                            expand=True
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_color=AppColors.ERROR,
                            icon_size=16,
                            tooltip=f"Remove {fname}",
                            style=button_hover_style,
                            on_click=make_remove_handler(path)
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                )
                files_list_column.controls.append(row_control)

    def remove_single_file(path_to_remove):
        if path_to_remove in selected_files:
            selected_files.remove(path_to_remove)
        render_files_list()
        page.update()

    async def invoke_files_picker(e):
        files = await ft.FilePicker().pick_files(
            allow_multiple=True,
            allowed_extensions=["xlsx", "xls"],
            dialog_title="Select Excel Files"
        )
        if files:
            for f in files:
                if f.path and f.path not in selected_files:
                    selected_files.append(f.path)
            render_files_list()
            page.update()

    async def invoke_output_picker(e):
        nonlocal output_folder_path
        folder_path = await ft.FilePicker().get_directory_path(dialog_title="Select Output Folder")
        if folder_path:
            output_folder_path = folder_path
            selected_output_txt.value = folder_path
            page.update()

    def reset_selected_files(e):
        selected_files.clear()
        render_files_list()
        status_text.value = "Selected files reset."
        status_text.color = AppColors.TEXT_MUTED
        page.update()

    def reset_output_folder(e):
        nonlocal output_folder_path
        output_folder_path = ""
        selected_output_txt.value = "No output folder selected"
        status_text.value = "Output folder reset."
        status_text.color = AppColors.TEXT_MUTED
        page.update()

    btn_select_files = ft.Button(
        "Select Excel Files",
        icon=ft.Icons.FILE_UPLOAD,
        style=button_hover_style,
        on_click=invoke_files_picker
    )

    btn_reset_files = ft.IconButton(
        icon=ft.Icons.RESTART_ALT,
        icon_color=AppColors.ERROR,
        tooltip="Reset Selected Files",
        style=button_hover_style,
        on_click=reset_selected_files
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

    terminal = TerminalWindow(page)
    progress_bar = ft.ProgressBar(visible=False, color=AppColors.PRIMARY)
    run_btn = ft.Button("Run File Merge", icon=ft.Icons.MERGE_TYPE, style=primary_button_style())

    async def run_merge(e):
        if not selected_files:
            status_text.value = "Please select Excel files to merge!"
            status_text.color = AppColors.ERROR
            page.update()
            return

        if not output_folder_path:
            status_text.value = "Please select an output folder!"
            status_text.color = AppColors.ERROR
            page.update()
            return

        filename = output_filename_input.value.strip() or "Merged_Data.xlsx"

        status_text.value = "Merging files..."
        status_text.color = AppColors.WARNING
        
        terminal.clear()
        terminal.append_line(f"Starting merge of {len(selected_files)} Excel files...")
        
        run_btn.disabled = True
        progress_bar.visible = True
        page.update()

        try:
            command = [
                sys.executable, "-u", os.path.join("src", "merge_excel.py"), 
                *selected_files, output_folder_path, filename
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
                status_text.value = "Excel files merged successfully!"
                status_text.color = AppColors.SUCCESS
                page.snack_bar = ft.SnackBar(content=ft.Text("✅ File merge completed!"), bgcolor=ft.Colors.GREEN_800)
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

    run_btn.on_click = run_merge

    files_card = create_card(
        ft.Column([
            ft.Row([btn_select_files, btn_reset_files, selected_files_txt], alignment=ft.MainAxisAlignment.START, spacing=10),
            files_list_container,
            ft.Row([btn_select_output, btn_reset_output, selected_output_txt], alignment=ft.MainAxisAlignment.START, spacing=10),
            output_filename_input
        ], spacing=10),
        title="File Merge Configuration",
        icon=ft.Icons.MERGE_TYPE
    )

    return ft.ListView([
        ft.Text("Excel File Merger", size=22, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN),
        status_text,
        ft.Container(height=10),
        files_card,
        run_btn,
        progress_bar,
        terminal.get_control()
    ], spacing=15, padding=20)

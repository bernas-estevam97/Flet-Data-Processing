import flet as ft
import subprocess
import sys
import asyncio
import os
import json

def main(page: ft.Page):
    # 1. App Configuration
    page.title = "Data processing - MotoRater"
    page.theme_mode = ft.ThemeMode.SYSTEM 
    page.window_width = 1000 
    page.window_height = 800 
    page.padding = 0
    hover_style = ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK)

    # ==========================================
    # 2. UI Components Setup (Data Filtering Page)
    # ==========================================
    status_text = ft.Text("System Ready", color=ft.Colors.BLUE_GREY_400)

    input_folder = ft.TextField(label="Data File Folder", border_color=ft.Colors.WHITE_70, read_only=True, expand=True)
    output_folder = ft.TextField(label="Output Folder", border_color=ft.Colors.WHITE_70, read_only=True, expand=True)

    selected_input_path = ft.Text("No folder selected", color=ft.Colors.CYAN_300, italic=True, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)
    selected_output_path = ft.Text("Defaults to input folder", color=ft.Colors.CYAN_300, italic=True, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)

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

    def clear_terminal(e):
        terminal_output.controls.clear()
        terminal_output.controls.append(ft.Text("Terminal cleared.", color=ft.Colors.WHITE_54, italic=True))
        page.update()

    clear_button = ft.IconButton(
        icon=ft.icons.Icons.DELETE, icon_color=ft.Colors.WHITE_54,
        tooltip="Clear Terminal", on_click=clear_terminal, icon_size=18, style=hover_style
    )

    terminal_output = ft.ListView(expand=True, spacing=2, auto_scroll=False)
    terminal_window = ft.Container(
        content=terminal_output, height=150, bgcolor=ft.Colors.BLACK_87,
        border_radius=5, padding=10, border=ft.Border.all(1, ft.Colors.WHITE_24)
    )

    terminal_section = ft.Column([
        ft.Row([
            ft.Text("Live Terminal Output", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE_70),
            clear_button
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        terminal_window
    ])

    # ==========================================
    # UI Components Setup (Statistics Page)
    # ==========================================
    def clear_stats_terminal(e):
        stats_terminal_output.controls.clear()
        stats_terminal_output.controls.append(ft.Text("Terminal cleared.", color=ft.Colors.WHITE_54, italic=True))
        page.update()

    stats_clear_button = ft.IconButton(
        icon=ft.icons.Icons.DELETE, icon_color=ft.Colors.WHITE_54,
        tooltip="Clear Terminal", on_click=clear_stats_terminal, icon_size=18, style=hover_style
    )

    stats_status_text = ft.Text("System Ready", color=ft.Colors.BLUE_GREY_400)

    stats_input_folder = ft.TextField(label="Filtered Data Folder", border_color=ft.Colors.WHITE_70, read_only=True, expand=True)
    stats_output_folder = ft.TextField(label="Output Folder (Optional)", border_color=ft.Colors.WHITE_70, read_only=True, expand=True)

    stats_selected_input_path = ft.Text("No folder selected", color=ft.Colors.CYAN_300, italic=True, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)
    stats_selected_output_path = ft.Text("Defaults to input folder", color=ft.Colors.CYAN_300, italic=True, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)

    stats_experiment_dropdown = ft.Dropdown(
        label="Experiment Type", value="footprint",
        options=[
            ft.dropdown.Option(key="footprint", text="Footprint"),
            ft.dropdown.Option(key="beam", text="Beam"),
            ft.dropdown.Option(key="swimming", text="Swimming"),
            ft.dropdown.Option(key="gridwalk", text="Gridwalk"),
        ], expand=True
    )

    stats_terminal_output = ft.ListView(expand=True, spacing=2, auto_scroll=False)
    stats_terminal_window = ft.Container(
        content=stats_terminal_output, height=150, bgcolor=ft.Colors.BLACK_87,
        border_radius=5, padding=10, border=ft.Border.all(1, ft.Colors.WHITE_24)
    )

    stats_terminal_section = ft.Column([
        ft.Row([
            ft.Text("Live Terminal Output", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE_70),
            stats_clear_button
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        stats_terminal_window
    ])

    # ==========================================
    # UI Components Setup (Statistics AIO Page)
    # ==========================================
    def clear_stats_terminal(e):
        stats_terminal_aio_output.controls.clear()
        stats_terminal_aio_output.controls.append(ft.Text("Terminal cleared.", color=ft.Colors.WHITE_54, italic=True))
        page.update()

    stats_clear_aio_button = ft.IconButton(
        icon=ft.icons.Icons.DELETE, icon_color=ft.Colors.WHITE_54,
        tooltip="Clear Terminal", on_click=clear_stats_terminal, icon_size=18, style=hover_style
    )

    stats_aio_status_text = ft.Text("System Ready", color=ft.Colors.BLUE_GREY_400)

    stats_input_aio_folder = ft.TextField(label="Filtered Data Folder", border_color=ft.Colors.WHITE_70, read_only=True, expand=True)
    stats_output_aio_folder = ft.TextField(label="Output Folder (Optional)", border_color=ft.Colors.WHITE_70, read_only=True, expand=True)

    stats_selected_input_aio_path = ft.Text("No folder selected", color=ft.Colors.CYAN_300, italic=True, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)
    stats_selected_output_aio_path = ft.Text("Defaults to input folder", color=ft.Colors.CYAN_300, italic=True, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)

    # ==========================================
    # NEW: Dynamic File Tagging Logic & UI
    # ==========================================
    
    # 1. State Dictionary to hold mappings for your backend script
    # e.g., {"F": "Female", "12W": "Timepoint 4"}
    active_file_tags = {} 
    
    # 2. UI Container to display the added tags visually
    tags_list_column = ft.Column(spacing=5) 
    
    # NEW: Define the container here and set visible=False initially
    tags_list_container = ft.Container(
        content=tags_list_column,
        padding=10,
        bgcolor=ft.Colors.BLACK_12,
        border_radius=5,
        border=ft.Border.all(1, ft.Colors.WHITE_24),
        visible=False # Starts hidden so you don't get the empty box
    )

    # 3. Input fields
    tag_code_input = ft.TextField(label="File Tag (e.g., F)", width=150, border_color=ft.Colors.WHITE_70)
    tag_meaning_input = ft.TextField(label="Meaning (e.g., Female)", width=300, border_color=ft.Colors.WHITE_70)

    # 4. Remove Tag Handler
    def remove_tag(e, code, row_control):
        if code in active_file_tags:
            del active_file_tags[code]
        tags_list_column.controls.remove(row_control)
        
        # NEW: If the list is empty after removing, hide the container again
        if len(tags_list_column.controls) == 0:
            tags_list_container.visible = False
            
        page.update()

    # 5. Add Tag Handler
    async def add_tag(e):
        code = tag_code_input.value.strip()
        meaning = tag_meaning_input.value.strip()

        if not code or not meaning:
            return
        if code in active_file_tags:
            return 

        active_file_tags[code] = meaning

        tag_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(f"Tag: [{code}]  ➔  Meaning: [{meaning}]", color=ft.Colors.CYAN_200, weight=ft.FontWeight.W_500),
            ]
        )
        
        delete_btn = ft.IconButton(
            icon=ft.icons.Icons.REMOVE_CIRCLE_OUTLINE,
            icon_color=ft.Colors.RED_400,
            tooltip="Remove Tag",
            on_click=lambda e, c=code, r=tag_row: remove_tag(e, c, r),
            style=hover_style
        )
        tag_row.controls.append(delete_btn)

        tags_list_column.controls.append(tag_row)
        
        # NEW: Ensure the container is visible once a tag is added
        tags_list_container.visible = True
        
        tag_code_input.value = ""
        tag_meaning_input.value = ""
        page.update()

        await tag_code_input.focus()

    add_tag_btn = ft.Button("Add", on_click=add_tag, icon=ft.icons.Icons.ADD, style=hover_style)

    # 6. Group the Tagging Section into a single component
    stats_tagging_section = ft.Column([
        ft.Text("Data Parsing Tags", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE_70),
        ft.Text("Define the filename abbreviations and their actual meanings for the processor.", size=12, color=ft.Colors.WHITE_54),
        ft.Row(
            [tag_code_input, tag_meaning_input, add_tag_btn], 
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            wrap=True
        ),
        # NEW: Just drop the container variable here
        tags_list_container 
    ])

    stats_terminal_aio_output = ft.ListView(expand=True, spacing=2, auto_scroll=False)
    stats_terminal_aio_window = ft.Container(
        content=stats_terminal_aio_output, height=150, bgcolor=ft.Colors.BLACK_87,
        border_radius=5, padding=10, border=ft.Border.all(1, ft.Colors.WHITE_24)
    )

    stats_terminal_aio_section = ft.Column([
        ft.Row([
            ft.Text("Live Terminal Output", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE_70),
            stats_clear_aio_button
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        stats_terminal_aio_window
    ])

    # ==========================================
    # UI Components Setup (Merge Page)
    # ==========================================
    def clear_merge_terminal(e):
        merge_terminal_output.controls.clear()
        merge_terminal_output.controls.append(ft.Text("Terminal cleared.", color=ft.Colors.WHITE_54, italic=True))
        page.update()

    merge_clear_button = ft.IconButton(
        icon=ft.icons.Icons.DELETE, icon_color=ft.Colors.WHITE_54,
        tooltip="Clear Terminal", on_click=clear_merge_terminal, icon_size=18, style=hover_style
    )

    merge_status_text = ft.Text("System Ready", color=ft.Colors.BLUE_GREY_400)

    # merge_file1_input = ft.TextField(label="First Excel File", border_color=ft.Colors.WHITE_70, read_only=True, expand=True)
    # merge_file2_input = ft.TextField(label="Second Excel File", border_color=ft.Colors.WHITE_70, read_only=True, expand=True)
    merge_output_folder = ft.TextField(label="Output Folder", border_color=ft.Colors.WHITE_70, read_only=True, expand=True)
    merge_output_filename = ft.TextField(label="Output File Name (e.g., merged_data.xlsx)", border_color=ft.Colors.WHITE_70, expand=True)

    # merge_selected_file1_path = ft.Text("No file selected", color=ft.Colors.CYAN_300, italic=True, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)
    # merge_selected_file2_path = ft.Text("No file selected", color=ft.Colors.CYAN_300, italic=True, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)
    merge_selected_output_path = ft.Text("No folder selected", color=ft.Colors.CYAN_300, italic=True, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)

    merge_terminal_output = ft.ListView(expand=True, spacing=2, auto_scroll=False)
    merge_terminal_window = ft.Container(
        content=merge_terminal_output, height=150, bgcolor=ft.Colors.BLACK_87,
        border_radius=5, padding=10, border=ft.Border.all(1, ft.Colors.WHITE_24)
    )

    merge_terminal_section = ft.Column([
        ft.Row([
            ft.Text("Live Terminal Output", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE_70),
            merge_clear_button
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        merge_terminal_window
    ])


    # ==========================================
    # 3. Directory & File Picker Logic
    # ==========================================
    # Filtering Pickers
    async def invoke_input_picker(e):
        folder_path = await ft.FilePicker().get_directory_path(dialog_title="Select Data Folder")
        if folder_path:
            selected_input_path.value = folder_path
            input_folder.value = folder_path
        page.update()

    async def invoke_output_picker(e):
        folder_path = await ft.FilePicker().get_directory_path(dialog_title="Select Output Folder")
        if folder_path:
            selected_output_path.value = folder_path
            output_folder.value = folder_path
        page.update()

    pick_input_button = ft.Button("Select Data Folder", icon=ft.Icons.FOLDER_OPEN, on_click=invoke_input_picker, style=hover_style)
    pick_output_button = ft.Button("Select Output Folder", icon=ft.Icons.FOLDER_OPEN, on_click=invoke_output_picker, style=hover_style)

    # Stats Pickers
    async def invoke_stats_input_picker(e):
        folder_path = await ft.FilePicker().get_directory_path(dialog_title="Select Filtered Data Folder")
        if folder_path:
            stats_selected_input_path.value = folder_path
            stats_input_folder.value = folder_path
        page.update()

    async def invoke_stats_output_picker(e):
        folder_path = await ft.FilePicker().get_directory_path(dialog_title="Select Output Folder")
        if folder_path:
            stats_selected_output_path.value = folder_path
            stats_output_folder.value = folder_path
        page.update()

    pick_stats_input_button = ft.Button("Select Filtered Folder", icon=ft.Icons.FOLDER_OPEN, on_click=invoke_stats_input_picker, style=hover_style)
    pick_stats_output_button = ft.Button("Select Output Folder", icon=ft.Icons.FOLDER_OPEN, on_click=invoke_stats_output_picker, style=hover_style)


    # Stats Pickers - AIO
    async def invoke_stats_aio_input_picker(e):
        folder_path = await ft.FilePicker().get_directory_path(dialog_title="Select Filtered Data Folder")
        if folder_path:
            stats_selected_input_aio_path.value = folder_path
            stats_input_aio_folder.value = folder_path
        page.update()

    async def invoke_stats_aio_output_picker(e):
        folder_path = await ft.FilePicker().get_directory_path(dialog_title="Select Output Folder")
        if folder_path:
            stats_selected_output_aio_path.value = folder_path
            stats_output_folder.value = folder_path
        page.update()

    pick_stats_aio_input_button = ft.Button("Select Filtered Folder", icon=ft.Icons.FOLDER_OPEN, on_click=invoke_stats_aio_input_picker, style=hover_style)
    pick_stats_aio_output_button = ft.Button("Select Output Folder", icon=ft.Icons.FOLDER_OPEN, on_click=invoke_stats_aio_output_picker, style=hover_style)

    # ==========================================
    # 🚀 NEW: Merge Pickers (Modern Awaitable Flet API)
    # ==========================================
    
    # Create a list to store the actual file paths in memory
    selected_merge_files = []

    # Create a UI Column to display the names of the selected files
    merge_selected_files_list = ft.Column(spacing=5)

    async def on_merge_files_picked(e):
    # 🚀 NEW: Await the file picker directly inside the click event!
        files = await ft.FilePicker().pick_files(
            allow_multiple=True, 
            allowed_extensions=["xlsx", "xls"]
        )
        
        selected_merge_files.clear()
        merge_selected_files_list.controls.clear()
        
        # If the user selected files (and didn't just hit 'Cancel')
        if files:
            for f in files:
                selected_merge_files.append(f.path)
                # Add a visual indicator for each file
                merge_selected_files_list.controls.append(
                    ft.Row([
                        ft.Icon(ft.Icons.INSERT_DRIVE_FILE, size=16, color=ft.Colors.BLUE_400),
                        ft.Text(f.name, size=14)
                    ])
                )
                
        e.page.update()
    

    async def invoke_merge_out_picker(e):
        folder_path = await ft.FilePicker().get_directory_path(dialog_title="Select Output Folder")
        if folder_path:
            merge_output_folder.value = folder_path
            merge_selected_output_path.value = folder_path
            page.update()

    # Buttons hooked directly to the async functions
    #merge_file_picker = ft.Button("Select Files", icon=ft.Icons.FILE_OPEN, on_click=on_merge_files_picked, style=hover_style)
    
    pick_merge_output_button = ft.Button("Select Output Folder", icon=ft.Icons.FOLDER_OPEN, on_click=invoke_merge_out_picker, style=hover_style)

    def clear_folder_selection(text_field, text_label, default_msg):
        text_field.value = ""
        text_label.value = default_msg
        page.update()

    def clear_merge_files(e):
        # print("Clear button clicked! Wiping files...") # Debugging check
        
        # 1. Clear the underlying data
        selected_merge_files.clear()
        
        # 2. Clear the visual UI column
        merge_selected_files_list.controls.clear()
        
        # 3. Add the placeholder text
        merge_selected_files_list.controls.append(
            ft.Text("No files selected", color=ft.Colors.WHITE_54, italic=True)
        )
        
        # 4. FORCE UPDATE the specific UI element (More reliable than page.update)
        merge_selected_files_list.update()

    # Clear Buttons logic and styling
    clear_in_btn = ft.IconButton(icon=ft.Icons.CLOSE, style=hover_style, tooltip="Clear", on_click=lambda e: clear_folder_selection(input_folder, selected_input_path, "No folder selected"))
    clear_out_btn = ft.IconButton(icon=ft.Icons.CLOSE, style=hover_style, tooltip="Clear", on_click=lambda e: clear_folder_selection(output_folder, selected_output_path, "Defaults to input folder"))
    clear_stats_in_btn = ft.IconButton(icon=ft.Icons.CLOSE, style=hover_style, tooltip="Clear", on_click=lambda e: clear_folder_selection(stats_input_folder, stats_selected_input_path, "No folder selected"))
    clear_stats_out_btn = ft.IconButton(icon=ft.Icons.CLOSE, style=hover_style, tooltip="Clear", on_click=lambda e: clear_folder_selection(stats_output_folder, stats_selected_output_path, "Defaults to input folder"))
    clear_stats_aio_in_btn = ft.IconButton(icon=ft.Icons.CLOSE, style=hover_style, tooltip="Clear", on_click=lambda e: clear_folder_selection(stats_input_aio_folder, stats_selected_input_aio_path, "No folder selected"))
    clear_stats_aio_out_btn = ft.IconButton(icon=ft.Icons.CLOSE, style=hover_style, tooltip="Clear", on_click=lambda e: clear_folder_selection(stats_output_aio_folder, stats_selected_output_aio_path, "Defaults to input folder"))

    # Merge clear buttons
    clear_merge_files_btn = ft.IconButton(
        icon=ft.Icons.CLOSE, 
        style=hover_style, 
        tooltip="Clear Selection", 
        on_click=clear_merge_files  # <-- Perfect Flet syntax
    )
    clear_merge_out_btn = ft.IconButton(icon=ft.Icons.CLOSE, style=hover_style, tooltip="Clear", on_click=lambda e: clear_folder_selection(merge_output_folder, merge_selected_output_path, "No folder selected"))

    # Run Buttons & Progress Bars
    run_filter_btn = ft.Button("Run Data Filtering", icon=ft.Icons.PLAY_ARROW, style=hover_style)
    filter_progress = ft.ProgressBar(visible=False, color=ft.Colors.AMBER_400)

    run_stats_btn = ft.Button("Run Descriptive Statistics", icon=ft.Icons.PLAY_ARROW, style=hover_style)
    stats_progress = ft.ProgressBar(visible=False, color=ft.Colors.AMBER_400)

    run_stats_aio_btn = ft.Button("Run Descriptive Statistics - AIO", icon=ft.Icons.PLAY_ARROW, style=hover_style)
    stats_aio_progress = ft.ProgressBar(visible=False, color=ft.Colors.AMBER_400)

    run_merge_btn = ft.Button("Run File Merge", icon=ft.Icons.PLAY_ARROW, style=hover_style)
    merge_progress = ft.ProgressBar(visible=False, color=ft.Colors.AMBER_400)


    # ==========================================
    # 4. Logic to run scripts 
    # ==========================================
    
    # --- Filter Script Logic ---
    async def run_script_excel_filtering(e):
        data_path = input_folder.value
        if not data_path:
            status_text.value = "Please select a data folder first!"
            status_text.color = ft.Colors.RED_400
            page.update()
            return

        out_path = output_folder.value if output_folder.value else ""
        choice = cutoff_dropdown.value
        animal = animal_dropdown.value
        experiment = experiment_dropdown.value
        camera = camera_dropdown.value

        status_text.value = "Processing... Please wait."
        status_text.color = ft.Colors.AMBER_400
        
        terminal_output.controls.clear()
        terminal_output.controls.append(ft.Text("Starting filtering script...", color=ft.Colors.GREEN_400, font_family="Consolas", selectable=True))
        
        run_filter_btn.disabled = True
        filter_progress.visible = True
        page.update()

        try:
            command = [
                sys.executable, "-u", "src/ex_filtering.py", 
                data_path, choice, animal, experiment, camera, out_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )

            line_count = 0
            MAX_LINES = 500  
            BATCH_SIZE = 10  
            
            while True:
                line = await process.stdout.readline()
                if not line:
                    page.update() 
                    if line_count > 0:
                        await terminal_output.scroll_to(offset=-1, duration=50)
                    break 
                
                decoded_line = line.decode('utf-8', errors='replace').strip()
                
                if decoded_line:
                    line_count += 1
                    line_color = ft.Colors.GREEN_400
                    if "[ERROR]" in decoded_line or "Traceback" in decoded_line or "Exception" in decoded_line:
                        line_color = ft.Colors.RED_400
                    elif "[WARNING]" in decoded_line:
                        line_color = ft.Colors.AMBER_400
                    
                    terminal_output.controls.append(
                        ft.Text(decoded_line, color=line_color, font_family="Consolas", selectable=True, size=12)
                    )
                    
                    if len(terminal_output.controls) > MAX_LINES:
                        del terminal_output.controls[0]
                    
                    if line_count % BATCH_SIZE == 0:
                        page.update() 
                        await terminal_output.scroll_to(offset=-1, duration=50) 

            await process.wait()

            if process.returncode == 0:
                status_text.value = "Filtering script executed successfully!"
                status_text.color = ft.Colors.GREEN_400
                page.snack_bar = ft.SnackBar(content=ft.Text("✅ Data filtering completed successfully!"), bgcolor=ft.Colors.GREEN_800)
                page.snack_bar.open = True
            else:
                status_text.value = f"Script failed with exit code {process.returncode}"
                status_text.color = ft.Colors.RED_400

        except Exception as err:
            status_text.value = f"Error: {err}"
            status_text.color = ft.Colors.RED_400
            terminal_output.controls.append(ft.Text(f"Error: {err}", color=ft.Colors.RED_400, font_family="Consolas", selectable=True))
            
        finally:
            run_filter_btn.disabled = False
            filter_progress.visible = False
            page.update()

    # --- Stats Script Logic ---
    async def run_script_excel_descriptive_stat(e):
        data_path = stats_input_folder.value
        if not data_path:
            stats_status_text.value = "Please select a filtered data folder first!"
            stats_status_text.color = ft.Colors.RED_400
            page.update()
            return

        out_path = stats_output_folder.value if stats_output_folder.value else ""
        experiment = stats_experiment_dropdown.value

        stats_status_text.value = "Generating statistics..."
        stats_status_text.color = ft.Colors.AMBER_400
        stats_terminal_output.controls.clear()
        stats_terminal_output.controls.append(ft.Text("Starting descriptive statistics script...", color=ft.Colors.GREEN_400, font_family="Consolas", selectable=True))
        
        run_stats_btn.disabled = True
        stats_progress.visible = True
        page.update()

        try:
            command = [
                sys.executable, "-u", "src/desc_analysis.py", 
                data_path, out_path, experiment
            ]
            
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )

            line_count = 0
            MAX_LINES = 500  
            BATCH_SIZE = 10  
            
            while True:
                line = await process.stdout.readline()
                if not line:
                    page.update() 
                    if line_count > 0:
                        await stats_terminal_output.scroll_to(offset=-1, duration=50)
                    break 
                
                decoded_line = line.decode('utf-8', errors='replace').strip()
                
                if decoded_line:
                    line_count += 1
                    line_color = ft.Colors.GREEN_400
                    if "[ERROR]" in decoded_line or "Traceback" in decoded_line or "Exception" in decoded_line:
                        line_color = ft.Colors.RED_400
                    elif "[WARNING]" in decoded_line:
                        line_color = ft.Colors.AMBER_400
                    
                    stats_terminal_output.controls.append(
                        ft.Text(decoded_line, color=line_color, font_family="Consolas", selectable=True, size=12)
                    )
                    
                    if len(stats_terminal_output.controls) > MAX_LINES:
                        del stats_terminal_output.controls[0]
                    
                    if line_count % BATCH_SIZE == 0:
                        page.update() 
                        await stats_terminal_output.scroll_to(offset=-1, duration=50) 
        
            await process.wait()

            if process.returncode == 0:
                stats_status_text.value = "Statistics generated successfully!"
                stats_status_text.color = ft.Colors.GREEN_400
                page.snack_bar = ft.SnackBar(content=ft.Text("✅ Descriptive statistics completed successfully!"), bgcolor=ft.Colors.GREEN_800)
                page.snack_bar.open = True
            else:
                stats_status_text.value = f"Script failed with exit code {process.returncode}"
                stats_status_text.color = ft.Colors.RED_400

        except Exception as err:
            stats_status_text.value = f"Error: {err}"
            stats_status_text.color = ft.Colors.RED_400
            stats_terminal_output.controls.append(ft.Text(f"Error: {err}", color=ft.Colors.RED_400, font_family="Consolas", selectable=True))
            
        finally:
            run_stats_btn.disabled = False
            stats_progress.visible = False
            page.update()

    # Descriptive analysis All In One - Different logic for extracting duration value and additional metadata
    async def run_script_excel_descriptive_stat_aio(e):
        data_path = stats_input_folder.value
        if not data_path:
            stats_aio_status_text.value = "Please select a filtered data folder first!"
            stats_aio_status_text.color = ft.Colors.RED_400
            page.update()
            return

        out_path = stats_output_aio_folder.value if stats_output_aio_folder.value else ""
        tags_json_string = json.dumps(active_file_tags)

        stats_aio_status_text.value = "Generating statistics..."
        stats_aio_status_text.color = ft.Colors.AMBER_400
        stats_terminal_output.controls.clear()
        stats_terminal_output.controls.append(ft.Text("Starting descriptive statistics AIO script...", color=ft.Colors.GREEN_400, font_family="Consolas", selectable=True))
        
        run_stats_btn.disabled = True
        stats_progress.visible = True
        page.update()

        try:
            command = [
                sys.executable, "-u", "src/desc_analysis_aio.py", 
                data_path, out_path, "Tagged_Experiment", tags_json_string
            ]
            
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )

            line_count = 0
            MAX_LINES = 500  
            BATCH_SIZE = 10  
            
            while True:
                line = await process.stdout.readline()
                if not line:
                    page.update() 
                    if line_count > 0:
                        await stats_terminal_output.scroll_to(offset=-1, duration=50)
                    break 
                
                decoded_line = line.decode('utf-8', errors='replace').strip()
                
                if decoded_line:
                    line_count += 1
                    line_color = ft.Colors.GREEN_400
                    if "[ERROR]" in decoded_line or "Traceback" in decoded_line or "Exception" in decoded_line:
                        line_color = ft.Colors.RED_400
                    elif "[WARNING]" in decoded_line:
                        line_color = ft.Colors.AMBER_400
                    
                    stats_terminal_output.controls.append(
                        ft.Text(decoded_line, color=line_color, font_family="Consolas", selectable=True, size=12)
                    )
                    
                    if len(stats_terminal_output.controls) > MAX_LINES:
                        del stats_terminal_output.controls[0]
                    
                    if line_count % BATCH_SIZE == 0:
                        page.update() 
                        await stats_terminal_output.scroll_to(offset=-1, duration=50) 
        
            await process.wait()

            if process.returncode == 0:
                stats_aio_status_text.value = "Statistics generated successfully!"
                stats_aio_status_text.color = ft.Colors.GREEN_400
                page.snack_bar = ft.SnackBar(content=ft.Text("✅ Descriptive statistics AIO completed successfully!"), bgcolor=ft.Colors.GREEN_800)
                page.snack_bar.open = True
            else:
                stats_aio_status_text.value = f"Script failed with exit code {process.returncode}"
                stats_aio_status_text.color = ft.Colors.RED_400

        except Exception as err:
            stats_aio_status_text.value = f"Error: {err}"
            stats_aio_status_text.color = ft.Colors.RED_400
            stats_terminal_output.controls.append(ft.Text(f"Error: {err}", color=ft.Colors.RED_400, font_family="Consolas", selectable=True))
            
        finally:
            run_stats_btn.disabled = False
            stats_progress.visible = False
            page.update()

    # Merge Script Logic
    async def run_script_merge_files(e):
        if len(selected_merge_files) < 2:
        # Show a snackbar or update status text alerting the user they need at least 2 files
            return
    
        out_folder = merge_output_folder.value # Or however you extract this
        out_file = merge_output_filename.value

        if not selected_merge_files or not out_folder or not out_file:
            merge_status_text.value = "Please fill in all paths and filenames first!"
            merge_status_text.color = ft.Colors.RED_400
            page.update()
            return

        merge_status_text.value = "Merging files... Please wait."
        merge_status_text.color = ft.Colors.AMBER_400
        merge_terminal_output.controls.clear()
        merge_terminal_output.controls.append(ft.Text("Starting merge script...", color=ft.Colors.GREEN_400, font_family="Consolas", selectable=True))
        
        run_merge_btn.disabled = True
        merge_progress.visible = True
        page.update()

        try:
            command = [
                sys.executable, "-u", "src/merge_excel.py", 
                *selected_merge_files, out_folder, out_file
            ]
            
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )

            line_count = 0
            MAX_LINES = 500  
            BATCH_SIZE = 10  
            
            while True:
                line = await process.stdout.readline()
                if not line:
                    page.update() 
                    if line_count > 0:
                        await merge_terminal_output.scroll_to(offset=-1, duration=50)
                    break 
                
                decoded_line = line.decode('utf-8', errors='replace').strip()
                
                if decoded_line:
                    line_count += 1
                    line_color = ft.Colors.GREEN_400
                    if "[ERROR]" in decoded_line or "Traceback" in decoded_line or "Exception" in decoded_line:
                        line_color = ft.Colors.RED_400
                    elif "[WARNING]" in decoded_line:
                        line_color = ft.Colors.AMBER_400
                    
                    merge_terminal_output.controls.append(
                        ft.Text(decoded_line, color=line_color, font_family="Consolas", selectable=True, size=12)
                    )
                    
                    if len(merge_terminal_output.controls) > MAX_LINES:
                        del merge_terminal_output.controls[0]
                    
                    if line_count % BATCH_SIZE == 0:
                        page.update() 
                        await merge_terminal_output.scroll_to(offset=-1, duration=50) 
        
            await process.wait()

            if process.returncode == 0:
                merge_status_text.value = "Files merged successfully!"
                merge_status_text.color = ft.Colors.GREEN_400
                page.snack_bar = ft.SnackBar(content=ft.Text("✅ Files merged successfully!"), bgcolor=ft.Colors.GREEN_800)
                page.snack_bar.open = True
            else:
                merge_status_text.value = f"Script failed with exit code {process.returncode}"
                merge_status_text.color = ft.Colors.RED_400

        except Exception as err:
            merge_status_text.value = f"Error: {err}"
            merge_status_text.color = ft.Colors.RED_400
            merge_terminal_output.controls.append(ft.Text(f"Error: {err}", color=ft.Colors.RED_400, font_family="Consolas", selectable=True))
            
        finally:
            run_merge_btn.disabled = False
            merge_progress.visible = False
            page.update()


    run_filter_btn.on_click = run_script_excel_filtering
    run_stats_btn.on_click = run_script_excel_descriptive_stat
    run_stats_aio_btn.on_click = run_script_excel_descriptive_stat_aio
    run_merge_btn.on_click = run_script_merge_files # Hooked up the new logic

    # ==========================================
    # 5. DEFINE THE DIFFERENT VIEWS (PAGES)
    # ==========================================
    
    tutorial_view = ft.Column(
        [
            ft.Container(
                content=ft.Column([
                    # Header Section
                    ft.Row([
                        ft.Icon(ft.Icons.ANALYTICS, size=40, color=ft.Colors.BLUE_400),
                        ft.Text("MotoRater Data Pipeline", size=32, weight=ft.FontWeight.BOLD),
                    ], alignment=ft.MainAxisAlignment.START),
                    
                    ft.Text(
                        "Welcome to the MotoRater automated data processing suite. This tool is designed to take your raw experimental data, apply rigorous filtering criteria, and generate clean, descriptive statistics.", 
                        color=ft.Colors.WHITE_70, size=16
                    ),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),

                    # Step 1: Filtering Card
                    ft.Card(
                        content=ft.Container(
                            padding=20,
                            content=ft.Column([
                                ft.ListTile(
                                    leading=ft.Icon(ft.Icons.FILTER_ALT, size=30, color=ft.Colors.CYAN_400),
                                    title=ft.Text("Step 1: Data Filtering", weight=ft.FontWeight.BOLD, size=20),
                                    subtitle=ft.Text("Process raw .xlsx files in bulk using parallel processing.")
                                ),
                                ft.Divider(),
                                ft.Markdown(
                                    """
* **Select Data Folder:** Choose the directory containing your raw `.xlsx` files.
* **Select Output Folder (Optional):** Define where the cleaned files will be saved. If left blank, it defaults to your input folder.
* **Set Parameters:** Carefully select your Cutoff, Animal Species, Experiment Type, and Camera Settings to match your lab setup.
* **Run:** Click **Run Data Filtering**. The system will process files simultaneously for maximum speed.
                                    """, 
                                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
                                )
                            ])
                        ),
                        elevation=2,
                    ),

                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),

                    # Step 2: Statistics Card
                    ft.Card(
                        content=ft.Container(
                            padding=20,
                            content=ft.Column([
                                ft.ListTile(
                                    leading=ft.Icon(ft.Icons.BAR_CHART, size=30, color=ft.Colors.PURPLE_400),
                                    title=ft.Text("Step 2: Descriptive Statistics", weight=ft.FontWeight.BOLD, size=20),
                                    subtitle=ft.Text("Generate summary statistics from your filtered datasets.")
                                ),
                                ft.Divider(),
                                ft.Markdown(
                                    """
* **Select Filtered Data Folder:** Choose the directory containing the `.xlsx` files you just processed in Step 1.
* **Select Output Folder (Optional):** Choose a destination for your final statistics blocks.
* **Select Experiment:** Ensure the experiment type matches your dataset for proper file naming.
* **Run:** Click **Run Descriptive Statistics** to compile the final analysis.
                                    """, 
                                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
                                )
                            ])
                        ),
                        elevation=2,
                    ),

                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),

                    # Step 3: Statistics Card AIO
                    ft.Card(
                        content=ft.Container(
                            padding=20,
                            content=ft.Column([
                                ft.ListTile(
                                    leading=ft.Icon(ft.Icons.BAR_CHART_ROUNDED, size=30, color=ft.Colors.PURPLE_400),
                                    title=ft.Text("Step 3: Descriptive AIO Statistics", weight=ft.FontWeight.BOLD, size=20),
                                    subtitle=ft.Text("Generate summary statistics from your filtered datasets.")
                                ),
                                ft.Divider(),
                                ft.Markdown(
                                    """
* **What will come out of this funciton?** If all your tags are properly presented in the name of each file, for example: F --> Female; WT -> Wild Type; Test -> FOOTPRINT, this script will filter each data file and present in new columns all the information regarding gender, test type and experimental group.                                    
* **Select Filtered Data Folder:** Choose the directory containing the `.xlsx` files you just processed in Step 1.
* **Select Output Folder (Optional):** Choose a destination for your final statistics blocks.
* **Select Experiment:** Ensure the experiment type matches your dataset for proper file naming.
* **Run:** Click **Run Descriptive AIO Statistics** to compile the final analysis.
                                    """, 
                                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
                                )
                            ])
                        ),
                        elevation=2,
                    ),

                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),

                    # 🚀 NEW: Step 4: Merge Card
                    ft.Card(
                        content=ft.Container(
                            padding=20,
                            content=ft.Column([
                                ft.ListTile(
                                    leading=ft.Icon(ft.Icons.CALL_MERGE, size=30, color=ft.Colors.ORANGE_400),
                                    title=ft.Text("Step 4: Merge Data (Optional)", weight=ft.FontWeight.BOLD, size=20),
                                    subtitle=ft.Text("Combine two identically structured Excel files into one single file.")
                                ),
                                ft.Divider(),
                                ft.Markdown(
                                    """
* **When to use this feature:** When you want to merge files from different experiments, time points, or conditions that share the same structure (sheets and columns).
* **Select all the files you want to merge:** Choose the two or more `.xlsx` files you wish to combine. They must share the same sheets and columns.
* **Select Output Folder:** Choose the destination folder for your newly merged file.
* **Output File Name:** Type the desired name for your new file (e.g., `combined_statistics.xlsx`).
* **Run:** Click **Run File Merge** to vertically stack the data from both files into a single master document.
                                    """, 
                                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
                                )
                            ])
                        ),
                        elevation=2,
                    ),

                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),

                    # Terminal Legend Card
                    ft.Card(
                        content=ft.Container(
                            padding=20,
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                            border_radius=10,
                            content=ft.Column([
                                ft.ListTile(
                                    leading=ft.Icon(ft.Icons.TERMINAL, size=30, color=ft.Colors.GREEN_400),
                                    title=ft.Text("Understanding the Live Terminal", weight=ft.FontWeight.BOLD, size=20),
                                ),
                                ft.Divider(),
                                ft.Row([
                                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_400, size=16),
                                    ft.Text("Green text:", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400),
                                    ft.Text("File processed successfully.")
                                ]),
                                ft.Row([
                                    ft.Icon(ft.Icons.WARNING, color=ft.Colors.AMBER_400, size=16),
                                    ft.Text("Amber text:", weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400),
                                    ft.Text("Warning or non-critical notification.")
                                ]),
                                ft.Row([
                                    ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_400, size=16),
                                    ft.Text("Red text:", weight=ft.FontWeight.BOLD, color=ft.Colors.RED_400),
                                    ft.Text("Error processing a file. Check the output for details.")
                                ]),
                            ])
                        ),
                        elevation=2,
                        
                    ),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                ]),
                padding=ft.Padding.only(right=20, top=10, bottom=20)
            )
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO
    )

    filtering_view = ft.Column(
        [
            ft.Container(
                content=ft.Column([
                    ft.Text("Data Filtering Setup", size=28, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT), 
                    
                    ft.Row(
                        [
                            ft.Column([ft.Row([pick_input_button, input_folder, clear_in_btn]), selected_input_path], expand=True),
                            ft.Column([ft.Row([pick_output_button, output_folder, clear_out_btn]), selected_output_path], expand=True)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.START 
                    ),
                    
                    ft.Divider(height=20),
                    ft.Text("Configuration Parameters", size=18, weight=ft.FontWeight.W_500),
                    ft.Row([cutoff_dropdown, animal_dropdown], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([experiment_dropdown, camera_dropdown], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    ft.Divider(height=20),
                    terminal_section,
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    
                    ft.Row([run_filter_btn], alignment=ft.MainAxisAlignment.CENTER, wrap=True),
                    ft.Row([filter_progress], alignment=ft.MainAxisAlignment.CENTER),
                    
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    status_text,
                ]),
                padding=ft.Padding.only(right=20)
            )
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO
    )

    stats_view = ft.Column(
        [
            ft.Container(
                content=ft.Column([
                    ft.Text("Descriptive Statistics", size=28, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    
                    ft.Row(
                        [
                            ft.Column([ft.Row([pick_stats_input_button, stats_input_folder, clear_stats_in_btn]), stats_selected_input_path], expand=True),
                            ft.Column([ft.Row([pick_stats_output_button, stats_output_folder, clear_stats_out_btn]), stats_selected_output_path], expand=True)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.START 
                    ),

                    ft.Divider(height=20),
                    ft.Text("Configuration Parameters", size=18, weight=ft.FontWeight.W_500),
                    ft.Row([stats_experiment_dropdown], alignment=ft.MainAxisAlignment.START),
                    
                    ft.Divider(height=20),
                    stats_terminal_section,
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),

                    ft.Row([run_stats_btn], alignment=ft.MainAxisAlignment.CENTER, wrap=True),
                    ft.Row([stats_progress], alignment=ft.MainAxisAlignment.CENTER),
                    
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    stats_status_text,
                ]),
                padding=ft.Padding.only(right=20)
            )
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO
    )


    stats_aio_view = ft.Column(
        [
            ft.Container(
                content=ft.Column([
                    ft.Text("Descriptive Statistics - AIO", size=28, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    
                    ft.Row(
                        [
                            ft.Column([ft.Row([pick_stats_aio_input_button, stats_input_aio_folder, clear_stats_aio_in_btn]), stats_selected_input_aio_path], expand=True),
                            ft.Column([ft.Row([pick_stats_aio_output_button, stats_output_aio_folder, clear_stats_aio_out_btn]), stats_selected_output_aio_path], expand=True)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.START 
                    ),

                    ft.Divider(height=20),
                    ft.Text("Tag Configuration", size=18, weight=ft.FontWeight.W_500),
                    ft.Row([stats_tagging_section], alignment=ft.MainAxisAlignment.START),
                    
                    ft.Divider(height=20),
                    stats_terminal_aio_section,
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),

                    ft.Row([run_stats_aio_btn], alignment=ft.MainAxisAlignment.CENTER, wrap=True),
                    ft.Row([stats_aio_progress], alignment=ft.MainAxisAlignment.CENTER),
                    
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    stats_status_text,
                ]),
                padding=ft.Padding.only(right=20)
            )
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO
    )

    # 🚀 NEW: Merged View Page Setup (Matching stats_aio_view layout)
    merge_view = ft.Column(
    [
        ft.Container(
            content=ft.Column([
                ft.Text("Merge Excel Files", size=28, weight=ft.FontWeight.BOLD),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                
                # Side-by-Side Input and Output Section
                ft.Row(
                    [
                        # --- LEFT COLUMN: INPUT FILES ---
                        ft.Column([
                            ft.Text("Input Files", size=16, weight=ft.FontWeight.W_500),
                            ft.Row([
                                # 🚀 UPDATED: Pointed directly to your async function!
                                ft.Button(
                                    "Select Files", 
                                    icon=ft.Icons.FOLDER_OPEN,
                                    on_click=on_merge_files_picked,
                                    style=hover_style
                                ),
                                clear_merge_files_btn  # Your pre-defined clear button
                            ]),
                            # Container for the dynamically growing list of files
                            ft.Container(
                                content=merge_selected_files_list,
                                padding=ft.Padding.only(left=5, top=5)
                            )
                        ], expand=True),

                        # --- RIGHT COLUMN: OUTPUT CONFIGURATION ---
                        ft.Column([
                            ft.Text("Output Configuration", size=16, weight=ft.FontWeight.W_500),
                            ft.Row([pick_merge_output_button, merge_output_folder, clear_merge_out_btn]),
                            merge_selected_output_path,
                            
                            ft.Divider(height=5, color=ft.Colors.TRANSPARENT), # Subtle spacing
                            
                            merge_output_filename,
                            ft.Text("Make sure to include .xlsx", color=ft.Colors.WHITE_54, italic=True)
                        ], expand=True)
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START 
                ),
                
                ft.Divider(height=20),
                merge_terminal_section,
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),

                ft.Row([run_merge_btn], alignment=ft.MainAxisAlignment.CENTER, wrap=True),
                ft.Row([merge_progress], alignment=ft.MainAxisAlignment.CENTER),
                
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                merge_status_text,
            ]),
            padding=ft.Padding.only(right=20)
        )
    ],
    expand=True,
    scroll=ft.ScrollMode.AUTO
)


    # ==========================================
    # 6. SIDEBAR & THEME TOGGLE LOGIC
    # ==========================================
    
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
        tooltip="Switch to Light Mode" if is_system_dark else "Switch to Dark Mode", style=hover_style
    )

    main_content_area = ft.Container(
        content=tutorial_view, 
        expand=True,
        padding=30
    )

    # 🚀 NEW: Hook up the new view index
    def on_nav_change(e):
        index = e.control.selected_index
        if index == 0:
            main_content_area.content = tutorial_view
        elif index == 1:
            main_content_area.content = filtering_view
        elif index == 2:
            main_content_area.content = stats_view
        elif index == 3:
            main_content_area.content = stats_aio_view # Added Route
        elif index == 4:
            main_content_area.content = merge_view # Added Route
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

    # 🚀 NEW: Added a new button into the sidebar navigation
    sidebar = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=400,
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

    sidebar_layout = ft.Column(
        [
            sidebar, 
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
    ft.run(main)
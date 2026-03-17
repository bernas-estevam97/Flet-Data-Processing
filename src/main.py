import flet as ft
import subprocess
import sys

def main(page: ft.Page):
    # 1. App Configuration
    page.title = "MR - Data processing"
    
    # --- NEW: Set to SYSTEM to respect user's default OS preference ---
    page.theme_mode = ft.ThemeMode.SYSTEM 
    
    page.window_width = 1000 
    page.window_height = 800 
    page.padding = 0 

    # ==========================================
    # 2. UI Components Setup (Data Filtering Page)
    # ==========================================
    status_text = ft.Text("System Ready", color=ft.Colors.BLUE_GREY_400)

    input_folder = ft.TextField(label="Data File Folder", border_color=ft.Colors.WHITE_70, read_only=True, expand=True)
    output_folder = ft.TextField(label="Output Folder", border_color=ft.Colors.WHITE_70, read_only=True, expand=True)

    selected_input_path = ft.Text("No folder selected", color=ft.Colors.CYAN_300, italic=True, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)
    selected_output_path = ft.Text("No folder selected", color=ft.Colors.CYAN_300, italic=True, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)

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

    # ==========================================
    # Terminal UI Components (Filtering Page)
    # ==========================================
    def clear_terminal(e):
        terminal_output.controls.clear()
        terminal_output.controls.append(ft.Text("Terminal cleared.", color=ft.Colors.WHITE_54, italic=True))
        e.control.page.update()

    clear_button = ft.IconButton(
        icon=ft.icons.Icons.DELETE, icon_color=ft.Colors.WHITE_54,
        tooltip="Clear Terminal", on_click=clear_terminal, icon_size=18
    )

    terminal_output = ft.ListView(expand=True, spacing=2, auto_scroll=True)
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
        e.control.page.update()

    stats_clear_button = ft.IconButton(
        icon=ft.icons.Icons.DELETE, icon_color=ft.Colors.WHITE_54,
        tooltip="Clear Terminal", on_click=clear_stats_terminal, icon_size=18
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

    stats_terminal_output = ft.ListView(expand=True, spacing=2, auto_scroll=True)
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
    # 3. Directory Picker Logic
    # ==========================================
    async def invoke_input_picker(e):
        folder_path = await ft.FilePicker().get_directory_path(dialog_title="Select Data Folder")
        if folder_path:
            selected_input_path.value = folder_path
            input_folder.value = folder_path
        else:
            selected_input_path.value = "Selection cancelled"
        page.update()

    async def invoke_output_picker(e):
        folder_path = await ft.FilePicker().get_directory_path(dialog_title="Select Output Folder")
        if folder_path:
            selected_output_path.value = folder_path
            output_folder.value = folder_path
        else:
            selected_output_path.value = "Selection cancelled"
        page.update()

    pick_input_button = ft.Button("Select Data Folder", icon=ft.Icons.FOLDER_OPEN, on_click=invoke_input_picker)
    pick_output_button = ft.Button("Select Output Folder", icon=ft.Icons.FOLDER_OPEN, on_click=invoke_output_picker)

    async def invoke_stats_input_picker(e):
        folder_path = await ft.FilePicker().get_directory_path(dialog_title="Select Filtered Data Folder")
        if folder_path:
            stats_selected_input_path.value = folder_path
            stats_input_folder.value = folder_path
        else:
            stats_selected_input_path.value = "Selection cancelled"
        page.update()

    async def invoke_stats_output_picker(e):
        folder_path = await ft.FilePicker().get_directory_path(dialog_title="Select Output Folder")
        if folder_path:
            stats_selected_output_path.value = folder_path
            stats_output_folder.value = folder_path
        else:
            stats_selected_output_path.value = "Defaults to input folder"
        page.update()

    pick_stats_input_button = ft.Button("Select Filtered Folder", icon=ft.Icons.FOLDER_OPEN, on_click=invoke_stats_input_picker)
    pick_stats_output_button = ft.Button("Select Output Folder", icon=ft.Icons.FOLDER_OPEN, on_click=invoke_stats_output_picker)

    # ==========================================
    # 4. Logic to run your scripts 
    # ==========================================
    def run_script_excel_filtering(e):
        data_path = input_folder.value
        if not data_path:
            status_text.value = "Please select a data folder first!"
            status_text.color = ft.Colors.RED_400
            page.update()
            return

        choice = cutoff_dropdown.value
        animal = animal_dropdown.value
        experiment = experiment_dropdown.value
        camera = camera_dropdown.value

        status_text.value = "Processing... Please wait."
        status_text.color = ft.Colors.AMBER_400
        
        terminal_output.controls.clear()
        terminal_output.controls.append(ft.Text("Starting filtering script...", color=ft.Colors.GREEN_400, font_family="Consolas", selectable=True))
        page.update()

        try:
            command = [
                sys.executable, "-u", "src/ex_filtering.py", 
                data_path, choice, animal, experiment, camera
            ]
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8', errors='replace', text=True, bufsize=1
            )
            for line in iter(process.stdout.readline, ''):
                if line:
                    terminal_output.controls.append(
                        ft.Text(line.strip(), color=ft.Colors.GREEN_400, font_family="Consolas",selectable=True, size=12)
                    )
                    page.update() 
            process.stdout.close()
            process.wait()

            if process.returncode == 0:
                status_text.value = "Filtering script executed successfully!"
                status_text.color = ft.Colors.GREEN_400
            else:
                status_text.value = f"Script failed with exit code {process.returncode}"
                status_text.color = ft.Colors.RED_400

        except Exception as err:
            status_text.value = f"Error: {err}"
            status_text.color = ft.Colors.RED_400
            terminal_output.controls.append(ft.Text(f"Error: {err}", color=ft.Colors.RED_400, font_family="Consolas", selectable=True))
            
        page.update()

    def run_script_excel_descriptive_stat(e):
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
        page.update()

        try:
            command = [
                sys.executable, "-u", "src/desc_analysis.py", 
                data_path, out_path, experiment
            ]
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8', errors='replace', text=True, bufsize=1
            )
            for line in iter(process.stdout.readline, ''):
                if line:
                    stats_terminal_output.controls.append(
                        ft.Text(line.strip(), color=ft.Colors.GREEN_400, font_family="Consolas", selectable=True, size=12)
                    )
                    page.update() 
            process.stdout.close()
            process.wait()

            if process.returncode == 0:
                stats_status_text.value = "Statistics generated successfully!"
                stats_status_text.color = ft.Colors.GREEN_400
            else:
                stats_status_text.value = f"Script failed with exit code {process.returncode}"
                stats_status_text.color = ft.Colors.RED_400

        except Exception as err:
            stats_status_text.value = f"Error: {err}"
            stats_status_text.color = ft.Colors.RED_400
            stats_terminal_output.controls.append(ft.Text(f"Error: {err}", color=ft.Colors.RED_400, font_family="Consolas", selectable=True))
            
        page.update()

    # ==========================================
    # 5. DEFINE THE DIFFERENT VIEWS (PAGES)
    # ==========================================

    tutorial_view = ft.Column(
        [
            ft.Text("Welcome to MotoRater Data Processing", size=28, weight=ft.FontWeight.BOLD),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            ft.Markdown(
                """
## How to use this application:
---
#### 1. Data Filtering
1. **Select Data Folder:** Click the folder icon to select the directory containing your raw `.xlsx` files.
2. **Select Output Folder:** (Optional) Choose where the processed files will be saved.
3. **Set Parameters:** Use the dropdowns to match the exact configuration of your experiment.
4. **Run Script:** Press the button to begin filtering. Watch the Live Terminal for updates!

---

#### 2. Descriptive Statistics
1. **Select Filtered Data:** Choose the folder containing your previously filtered `.xlsx` files.
2. **Select Output Folder:** (Optional) If left blank, it will save directly alongside your input files.
3. **Select Experiment:** Choose the experiment type for the final file naming convention.
4. **Run Script:** Press the button to generate your summary statistics block.
                """,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
            )
        ],
        expand=True,
    )

    filtering_view = ft.Column(
        [
            ft.Text("Data Filtering Setup", size=28, weight=ft.FontWeight.BOLD),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT), 
            
            ft.Row(
                [
                    ft.Column([ft.Row([pick_input_button, input_folder]), selected_input_path], expand=True),
                    ft.Column([ft.Row([pick_output_button, output_folder]), selected_output_path], expand=True)
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
            
            ft.Row(
                [ft.Button("Run Data Filtering", icon=ft.Icons.PLAY_ARROW, on_click=run_script_excel_filtering)],
                alignment=ft.MainAxisAlignment.CENTER, wrap=True 
            ),
            
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            status_text,
        ],
        expand=True,
    )

    stats_view = ft.Column(
        [
            ft.Text("Descriptive Statistics", size=28, weight=ft.FontWeight.BOLD),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            
            ft.Row(
                [
                    ft.Column([ft.Row([pick_stats_input_button, stats_input_folder]), stats_selected_input_path], expand=True),
                    ft.Column([ft.Row([pick_stats_output_button, stats_output_folder]), stats_selected_output_path], expand=True)
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

            ft.Row(
                [ft.Button("Run Descriptive Statistics", icon=ft.Icons.PLAY_ARROW, on_click=run_script_excel_descriptive_stat)],
                alignment=ft.MainAxisAlignment.CENTER, wrap=True 
            ),
            
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            stats_status_text,
        ],
        expand=True
    )

    # ==========================================
    # 6. SIDEBAR & THEME TOGGLE LOGIC
    # ==========================================
    
    # Check the actual system theme to set the initial toggle icon accurately
    is_system_dark = page.platform_brightness == ft.Brightness.DARK

    def toggle_theme(e):
        # Resolve what the current effective theme is
        current_is_dark = page.theme_mode == ft.ThemeMode.DARK or (
            page.theme_mode == ft.ThemeMode.SYSTEM and page.platform_brightness == ft.Brightness.DARK
        )
        
        # Swap it
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
        tooltip="Switch to Light Mode" if is_system_dark else "Switch to Dark Mode"
    )

    main_content_area = ft.Container(
        content=tutorial_view, 
        expand=True,
        padding=30
    )

    def on_nav_change(e):
        index = e.control.selected_index
        if index == 0:
            main_content_area.content = tutorial_view
        elif index == 1:
            main_content_area.content = filtering_view
        elif index == 2:
            main_content_area.content = stats_view
        page.update()

    sidebar = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=400,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.HELP_OUTLINE, selected_icon=ft.Icons.HELP, label="Tutorial"),
            ft.NavigationRailDestination(icon=ft.Icons.FILTER_ALT_OUTLINED, selected_icon=ft.Icons.FILTER_ALT, label="Data Filtering"),
            ft.NavigationRailDestination(icon=ft.Icons.BAR_CHART_OUTLINED, selected_icon=ft.Icons.BAR_CHART, label="Statistics"),
        ],
        on_change=on_nav_change,
        expand=True # <-- NEW: This forces the navigation rail to stretch down
    )

    # --- NEW: We wrap the sidebar and the button in a single column ---
    sidebar_layout = ft.Column(
        [
            sidebar, 
            # We add a little padding to the bottom so the button isn't hugging the window edge
            ft.Container(content=theme_icon_button, padding=ft.Padding.only(bottom=20)) 
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

    # Assemble the final page layout using our new sidebar_layout
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
import flet as ft
import subprocess

def main(page: ft.Page):
    # 1. App Configuration
    page.title = "MR - Data processing"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 850
    page.window_height = 800 
    page.padding = 30

    # 2. UI Components Setup
    status_text = ft.Text("System Ready", color=ft.Colors.BLUE_GREY_400)

    # --- NEW: Added read_only=True to block typing, and expand=True to fill row space ---
    input_folder = ft.TextField(label="Data File Folder", border_color=ft.Colors.WHITE_70, read_only=True, expand=True)
    output_folder = ft.TextField(label="Output Folder", border_color=ft.Colors.WHITE_70, read_only=True, expand=True)

    selected_input_path = ft.Text(
        "No folder selected", color=ft.Colors.CYAN_300, italic=True, 
        overflow=ft.TextOverflow.ELLIPSIS, max_lines=1, expand=True
    )
    
    selected_output_path = ft.Text(
        "No folder selected", color=ft.Colors.CYAN_300, italic=True, 
        overflow=ft.TextOverflow.ELLIPSIS, max_lines=1, expand=True
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

    # Terminal UI Setup
    terminal_output = ft.ListView(expand=True, spacing=2, auto_scroll=True)
    terminal_window = ft.Container(
        content=terminal_output, height=150, bgcolor=ft.Colors.BLACK_87,
        border_radius=5, padding=10, border=ft.Border.all(1, ft.Colors.WHITE_24)
    )

    # --- 3. Directory Picker Logic ---
    async def invoke_input_picker(e):
        folder_path = await ft.FilePicker().get_directory_path(dialog_title="Select Data Folder")
        
        if folder_path:
            selected_input_path.value = folder_path
            #selected_input_path.tooltip = folder_path  # Tooltip for truncated paths
            input_folder.value = folder_path
        else:
            selected_input_path.value = "Selection cancelled"
            #selected_input_path.tooltip = None
            
        page.update()

    async def invoke_output_picker(e):
        folder_path = await ft.FilePicker().get_directory_path(dialog_title="Select Output Folder")
        
        if folder_path:
            selected_output_path.value = folder_path
            #selected_output_path.tooltip = folder_path # Tooltip for truncated paths
            output_folder.value = folder_path
        else:
            selected_output_path.value = "Selection cancelled"
            #selected_output_path.tooltip = None
            
        page.update()

    pick_input_button = ft.Button("Select Data Folder", icon=ft.Icons.FOLDER_OPEN, on_click=invoke_input_picker)
    pick_output_button = ft.Button("Select Output Folder", icon=ft.Icons.FOLDER_OPEN, on_click=invoke_output_picker)

    # 4. Logic to run your scripts 
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
        terminal_output.controls.append(ft.Text("Starting script...", color=ft.Colors.GREEN_400, font_family="monospace"))
        page.update()

        try:
            command = [
                "python", "-u", "src/new_excel_filtering_all.py", 
                data_path, choice, animal, experiment, camera
            ]

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for line in iter(process.stdout.readline, ''):
                if line:
                    terminal_output.controls.append(
                        ft.Text(line.strip(), color=ft.Colors.GREEN_400, font_family="monospace", size=12)
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
            terminal_output.controls.append(ft.Text(f"Error: {err}", color=ft.Colors.RED_400, font_family="monospace"))
            
        page.update()

    def run_script_excel_descriptive_stat(e):
        pass 

    # 5. Build the Layout
    page.add(
        ft.Column(
            [
                ft.Text("MotoRater - Data processing", size=28, weight=ft.FontWeight.BOLD),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT), 
                
                # --- NEW: Layout grouping (Button -> Input -> Text Below) ---
                ft.Row(
                    [
                        # Left side for Input Folder
                        ft.Column(
                            [
                                ft.Row([pick_input_button, input_folder]), # Button on left, text field on right
                                #selected_input_path                        # Tooltip label below
                            ], 
                            expand=True
                        ),
                        
                        # Right side for Output Folder
                        ft.Column(
                            [
                                ft.Row([pick_output_button, output_folder]), # Button on left, text field on right
                                #selected_output_path                         # Tooltip label below
                            ], 
                            expand=True
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START 
                ),
                
                ft.Divider(height=20),
                
                ft.Text("Configuration Parameters", size=18, weight=ft.FontWeight.W_500),
                ft.Row([cutoff_dropdown, animal_dropdown], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([experiment_dropdown, camera_dropdown], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Divider(height=20),
                
                ft.Text("Live Terminal Output", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE_70),
                terminal_window,

                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                
                ft.Row(
                    [
                        ft.Button("Run Data Filtering", icon=ft.Icons.PLAY_ARROW, on_click=run_script_excel_filtering),
                        ft.Button("Run Descriptive Statistics", icon=ft.Icons.PLAY_ARROW, on_click=run_script_excel_descriptive_stat),
                        ft.Button("Run Backup Script", icon=ft.Icons.BACKUP),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER, wrap=True 
                ),
                
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                status_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )

if __name__ == "__main__":
    ft.run(main)
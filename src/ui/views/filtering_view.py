import flet as ft
from ui.theme import AppColors, create_card, button_hover_style, primary_button_style, danger_button_style
from ui.terminal import TerminalWindow
from process_manager import process_manager, start_task

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

    def hint(text=""):
        return ft.Text(text, size=12, color=AppColors.TEXT_MUTED)

    # --- Floor reference ---
    floor_dropdown = ft.Dropdown(
        label="Floor Reference", value="auto",
        options=[
            ft.dropdown.Option(key="auto", text="Auto (measured per session)"),
            ft.dropdown.Option(key="fixed", text="Fixed (species / camera constants)"),
        ], expand=True
    )
    floor_hint = hint()

    def update_floor_hint(e=None):
        if floor_dropdown.value == "auto":
            floor_hint.value = ("Floor = resting level of the hind toe in each file. Heights stay correct "
                                "when the camera or setup moves between sessions.")
        else:
            floor_hint.value = ("Uses the stored constant for the selected species, experiment and camera "
                                "settings. Combinations without a constant are left as is.")
        if e is not None:
            page.update()

    floor_dropdown.on_select = update_floor_hint
    update_floor_hint()

    height_cutoff_switch = ft.Switch(
        label="Apply Hind Paw Height Cutoff",
        value=False,
        active_color=AppColors.PRIMARY,
        tooltip="Blank height, clearance and drag values after the hind paw passes the camera threshold"
    )

    # --- Paw swing detection ---
    # Keep in sync with SWING_SPEED_BY_EXPERIMENT / SWING_SPEED_DEFAULT in ex_filtering.py
    # (not imported here so the UI does not load pandas/scipy at startup).
    swing_defaults = {"groundwalk": 0.1, "gridwalk": 0.1, "beamwalk": 0.03}

    def default_swing():
        return str(swing_defaults.get(experiment_dropdown.value, 0.1))

    swing_input = ft.TextField(
        label="Swing Speed Threshold", value=default_swing(), width=220,
        suffix="m/s",
        input_filter=ft.InputFilter(regex_string=r"^\d*\.?\d*$", allow=True, replacement_string=""),
        tooltip="Paw speed above this value counts as swing. 0 keeps every frame."
    )
    swing_hint = hint()

    def read_swing():
        try:
            return float(swing_input.value)
        except (TypeError, ValueError):
            return None

    def update_swing_hint(e=None):
        value = read_swing()
        if value is None:
            swing_input.error = "Enter a number (0 or more)"
            swing_hint.value = ""
        else:
            swing_input.error = None
            exp_name = experiment_dropdown.value.capitalize()
            if value == 0:
                swing_hint.value = "0 m/s: every frame is kept, stance included."
            else:
                swing_hint.value = (f"Paw speed and acceleration are kept only where that paw moves faster than "
                                    f"{value} m/s (swing). Recommended for {exp_name}: {default_swing()} m/s.")
        if e is not None:
            page.update()

    def reset_swing(e=None):
        swing_input.value = default_swing()
        update_swing_hint(e)

    swing_input.on_change = update_swing_hint
    experiment_dropdown.on_select = reset_swing  # new experiment = its recommended threshold
    update_swing_hint()

    btn_reset_swing = ft.IconButton(
        icon=ft.Icons.RESTART_ALT,
        icon_color=AppColors.PRIMARY,
        tooltip="Use the recommended value for this experiment",
        style=button_hover_style,
        on_click=reset_swing
    )

    keep_positions_switch = ft.Switch(
        label="Keep Positions Sheet",
        value=True,
        active_color=AppColors.PRIMARY,
        tooltip="Copy the raw 'Positions (used)' sheet into each filtered file.\nTurn off for about 2x faster filtering when you don't need the positions."
    )

    TASK_ID = "filtering"

    terminal = TerminalWindow(page)
    progress_bar = ft.ProgressBar(visible=False, color=AppColors.PRIMARY)
    run_btn = ft.Button("Run Data Filtering", icon=ft.Icons.PLAY_ARROW, style=primary_button_style())
    stop_btn = ft.Button(
        "Force Stop",
        icon=ft.Icons.STOP_CIRCLE,
        style=danger_button_style(),
        disabled=True,
        tooltip="Force stop running processes"
    )

    async def stop_filtering(e):
        stop_btn.disabled = True
        status_text.value = "Stopping processes..."
        status_text.color = AppColors.WARNING
        terminal.append_line("[WARN] Stopping processes requested by user...")
        page.update()
        count = await process_manager.kill_all()
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"⏹️ Force stopped {count} running process(es)."),
            bgcolor=ft.Colors.AMBER_800
        )
        page.snack_bar.open = True
        page.update()

    stop_btn.on_click = stop_filtering

    async def run_filtering(e):
        if not input_folder_path:
            status_text.value = "Please select a data folder first!"
            status_text.color = AppColors.ERROR
            page.update()
            return

        swing_speed = read_swing()
        if swing_speed is None:
            status_text.value = "Please enter a valid swing speed threshold (0 or more)."
            status_text.color = AppColors.ERROR
            page.update()
            return

        out_path = output_folder_path if output_folder_path else input_folder_path
        choice = cutoff_dropdown.value
        animal = animal_dropdown.value
        experiment = experiment_dropdown.value
        camera = camera_dropdown.value
        height_cutoff = "yes" if height_cutoff_switch.value else "no"
        keep_positions = "yes" if keep_positions_switch.value else "no"

        status_text.value = "Processing... Please wait."
        status_text.color = AppColors.WARNING
        
        terminal.clear()
        terminal.append_line("Starting filtering script...")
        
        run_btn.disabled = True
        stop_btn.disabled = False
        progress_bar.visible = True
        page.update()

        try:
            process = await start_task("ex_filtering", [input_folder_path, choice, animal, experiment, camera, out_path, height_cutoff, keep_positions, floor_dropdown.value, str(swing_speed)])
            process_manager.register(TASK_ID, "Data Filtering", process)

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

            if process_manager.was_stopped_by_user(TASK_ID):
                status_text.value = "Process forcefully stopped by user."
                status_text.color = AppColors.WARNING
                terminal.append_line("[STOPPED] Filtering script terminated by user.")
            elif process.returncode == 0:
                status_text.value = "Filtering script executed successfully!"
                status_text.color = AppColors.SUCCESS
                page.snack_bar = ft.SnackBar(content=ft.Text("✅ Data filtering completed successfully!"), bgcolor=ft.Colors.GREEN_800)
                page.snack_bar.open = True
            else:
                status_text.value = f"Script failed with exit code {process.returncode}"
                status_text.color = AppColors.ERROR

        except Exception as err:
            if process_manager.was_stopped_by_user(TASK_ID):
                status_text.value = "Process forcefully stopped by user."
                status_text.color = AppColors.WARNING
                terminal.append_line("[STOPPED] Filtering script terminated by user.")
            else:
                status_text.value = f"Error: {err}"
                status_text.color = AppColors.ERROR
                terminal.append_line(f"[ERROR] {err}")
            
        finally:
            process_manager.unregister(TASK_ID)
            run_btn.disabled = False
            stop_btn.disabled = True
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
            ft.Row([experiment_dropdown, animal_dropdown], spacing=15),
            ft.Row([camera_dropdown, cutoff_dropdown], spacing=15),
            hint("Movement window starts when the selected marker first moves and ends when the nose stops."),
        ], spacing=15),
        title="Experiment Setup",
        icon=ft.Icons.SCIENCE
    )

    floor_card = create_card(
        ft.Column([
            ft.Row([floor_dropdown], spacing=15),
            floor_hint,
            height_cutoff_switch,
        ], spacing=10),
        title="Floor & Height Reference",
        icon=ft.Icons.HEIGHT
    )

    swing_card = create_card(
        ft.Column([
            ft.Row([swing_input, btn_reset_swing], spacing=5, vertical_alignment=ft.CrossAxisAlignment.START),
            swing_hint,
        ], spacing=10),
        title="Paw Swing Detection",
        icon=ft.Icons.DIRECTIONS_RUN
    )

    output_card = create_card(
        ft.Column([
            keep_positions_switch,
            hint("Kinematics are rebuilt from 'Positions (used)'. QC columns (tracked frames, step length SD, "
                 "hind ahead of front) are added to every file."),
        ], spacing=10),
        title="Output",
        icon=ft.Icons.SAVE_ALT
    )

    return ft.ListView([
        ft.Text("Data Filtering", size=22, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN),
        status_text,
        ft.Container(height=10),
        folder_card,
        params_card,
        floor_card,
        swing_card,
        output_card,
        ft.Row([run_btn, stop_btn], spacing=10),
        progress_bar,
        terminal.get_control()
    ], spacing=15, padding=20)

import flet as ft
import json
from ui.theme import AppColors, create_card, button_hover_style, primary_button_style, danger_button_style
from ui.terminal import TerminalWindow
from process_manager import process_manager, start_task

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

    # --- Column headers (new Excel columns) and file tags (codes found in file names) ---
    column_headers = []      # ordered: defines the column order in the output Excel
    active_file_tags = {}    # tag code -> column header

    new_column_input = ft.TextField(
        label="New column header name", hint_text="e.g. Gender", width=280,
        tooltip="Name of a new column in the output Excel file, e.g. Gender, Experimental Group, Test."
    )
    columns_row = ft.Row(wrap=True, spacing=8, run_spacing=8)
    columns_hint = ft.Text("No column headers yet.", size=12, italic=True, color=AppColors.TEXT_MUTED)

    tag_code_input = ft.TextField(
        label="Tag present in your data files", hint_text="e.g. F", width=280,
        tooltip="Code exactly as it appears in the file name, e.g. F, M, WT, TG, BEAM.\nThis code is written into the Excel cell."
    )
    column_dropdown = ft.Dropdown(
        label="Goes into column", width=280, disabled=True,
        tooltip="Pick one of the column headers you created above."
    )

    tags_list_column = ft.Column(spacing=5)
    tags_list_container = ft.Container(
        content=tags_list_column,
        padding=10,
        bgcolor=ft.Colors.BLACK_12,
        border_radius=5,
        border=ft.Border.all(1, AppColors.BORDER),
        visible=False
    )

    def refresh_tagging():
        """Rebuild column chips, dropdown options and the tag list from state."""
        columns_row.controls = [
            ft.Chip(
                label=ft.Text(col),
                delete_icon_color=AppColors.ERROR,
                on_delete=lambda _, c=col: remove_column(c),
            )
            for col in column_headers
        ]
        columns_hint.visible = not column_headers

        column_dropdown.options = [ft.dropdown.Option(key=col, text=col) for col in column_headers]
        column_dropdown.disabled = not column_headers
        if column_dropdown.value not in column_headers:
            column_dropdown.value = column_headers[-1] if column_headers else None

        tags_list_column.controls = [
            ft.Row([
                ft.Text(f"🏷️  {code} ➔ {col}", color=AppColors.PRIMARY, weight=ft.FontWeight.BOLD, size=13),
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_color=AppColors.ERROR,
                    icon_size=18,
                    style=button_hover_style,
                    tooltip=f"Remove tag '{code}'",
                    on_click=lambda _, c=code: remove_tag(c)
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            for col in column_headers
            for code, tag_col in active_file_tags.items() if tag_col == col
        ]
        tags_list_container.visible = bool(active_file_tags)
        page.update()

    def add_column(e):
        name = new_column_input.value.strip()
        if not name:
            return
        if name.lower() in (c.lower() for c in column_headers) or name.lower() in ("ids", "timepoint"):
            status_text.value = f"Column '{name}' already exists or is reserved."
            status_text.color = AppColors.ERROR
            page.update()
            return
        column_headers.append(name)
        column_dropdown.value = name
        new_column_input.value = ""
        refresh_tagging()

    def remove_column(col):
        column_headers.remove(col)
        for code in [c for c, tag_col in active_file_tags.items() if tag_col == col]:
            del active_file_tags[code]
        refresh_tagging()

    def remove_tag(code):
        active_file_tags.pop(code, None)
        refresh_tagging()

    def reset_all_tags(e):
        column_headers.clear()
        active_file_tags.clear()
        new_column_input.value = ""
        tag_code_input.value = ""
        column_dropdown.value = None
        status_text.value = "All column headers and tags cleared."
        status_text.color = AppColors.TEXT_MUTED
        refresh_tagging()

    def add_tag(e):
        code = tag_code_input.value.strip().upper()
        col = column_dropdown.value
        if not code:
            return
        if not col:
            status_text.value = "Create a column header first, then pick it from the dropdown."
            status_text.color = AppColors.ERROR
            page.update()
            return
        if code in active_file_tags:
            status_text.value = f"Tag '{code}' already goes into '{active_file_tags[code]}'."
            status_text.color = AppColors.ERROR
            page.update()
            return
        active_file_tags[code] = col
        tag_code_input.value = ""
        refresh_tagging()

    new_column_input.on_submit = add_column
    tag_code_input.on_submit = add_tag
    add_column_btn = ft.Button("Add Column", icon=ft.Icons.VIEW_COLUMN, style=button_hover_style, on_click=add_column)
    add_tag_btn = ft.Button("Add Tag", icon=ft.Icons.ADD, style=button_hover_style, on_click=add_tag)

    reset_tags_btn = ft.IconButton(
        icon=ft.Icons.CLEAR_ALL,
        icon_color=AppColors.ERROR,
        tooltip="Clear All Column Headers & Tags",
        style=button_hover_style,
        on_click=reset_all_tags
    )

    # --- Timepoint schedule (experimental protocol) ---
    start_week_input = ft.TextField(
        label="First timepoint (week)", value="4", width=180,
        input_filter=ft.NumbersOnlyInputFilter(),
        tooltip="Week of your first experiment, e.g. 2 for 2W."
    )
    interval_input = ft.TextField(
        label="Weeks between timepoints", value="4", width=200,
        input_filter=ft.NumbersOnlyInputFilter(),
        tooltip="How many weeks pass between experiments, e.g. 3 or 4."
    )
    schedule_preview = ft.Text(size=12, color=AppColors.TEXT_MUTED)

    def read_schedule():
        """Return (start_week, interval) or None if the inputs are invalid."""
        try:
            start, step = int(start_week_input.value), int(interval_input.value)
        except (TypeError, ValueError):
            return None
        return (start, step) if step >= 1 else None

    def update_schedule_preview(e=None):
        schedule = read_schedule()
        if schedule is None:
            schedule_preview.value = "Enter whole numbers (interval at least 1 week)."
            schedule_preview.color = AppColors.ERROR
        else:
            start, step = schedule
            schedule_preview.value = "Timepoint mapping: " + ", ".join(
                f"{start + i * step}W ➔ {i + 1}" for i in range(4)) + ", ..."
            schedule_preview.color = AppColors.TEXT_MUTED
        if e is not None:
            page.update()

    start_week_input.on_change = update_schedule_preview
    interval_input.on_change = update_schedule_preview
    update_schedule_preview()

    group_trials_switch = ft.Switch(
        label="Group Trials by Base ID & Tags (Calculate Means)",
        value=True,
        active_color=AppColors.PRIMARY,
        tooltip="Averages trial files sharing base subject ID and identified tags"
    )

    TASK_ID = "stats_aio"

    terminal = TerminalWindow(page)
    progress_bar = ft.ProgressBar(visible=False, color=AppColors.PRIMARY)
    run_btn = ft.Button("Run Descriptive AIO Statistics", icon=ft.Icons.AUTO_AWESOME, style=primary_button_style())
    stop_btn = ft.Button(
        "Force Stop",
        icon=ft.Icons.STOP_CIRCLE,
        style=danger_button_style(),
        disabled=True,
        tooltip="Force stop running processes"
    )

    async def stop_stats_aio(e):
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

    stop_btn.on_click = stop_stats_aio

    async def run_stats_aio(e):
        if not input_folder_path:
            status_text.value = "Please select a filtered data folder first!"
            status_text.color = AppColors.ERROR
            page.update()
            return

        schedule = read_schedule()
        if schedule is None:
            status_text.value = "Timepoint schedule needs whole numbers (interval at least 1 week)."
            status_text.color = AppColors.ERROR
            page.update()
            return
        start_week, interval = schedule

        out_path = output_folder_path if output_folder_path else input_folder_path
        # Order tags by column so output columns follow the order the user created them
        ordered_tags = {code: col for col in column_headers for code, c in active_file_tags.items() if c == col}
        tags_json_string = json.dumps(ordered_tags)
        should_group = "y" if group_trials_switch.value else "n"

        status_text.value = "Generating AIO statistics..."
        status_text.color = AppColors.WARNING
        
        terminal.clear()
        terminal.append_line("Starting descriptive statistics AIO script...")
        
        run_btn.disabled = True
        stop_btn.disabled = False
        progress_bar.visible = True
        page.update()

        try:
            process = await start_task("desc_analysis_aio", [input_folder_path, out_path, "Tagged_Experiment", tags_json_string, should_group, str(start_week), str(interval)])
            process_manager.register(TASK_ID, "AIO Statistics", process)

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
                terminal.append_line("[STOPPED] AIO Statistics script terminated by user.")
            elif process.returncode == 0:
                status_text.value = "AIO Descriptive statistics completed successfully!"
                status_text.color = AppColors.SUCCESS
                page.snack_bar = ft.SnackBar(content=ft.Text("✅ Tagged AIO Statistics completed!"), bgcolor=ft.Colors.GREEN_800)
                page.snack_bar.open = True
            else:
                status_text.value = f"Script failed with exit code {process.returncode}"
                status_text.color = AppColors.ERROR

        except Exception as err:
            if process_manager.was_stopped_by_user(TASK_ID):
                status_text.value = "Process forcefully stopped by user."
                status_text.color = AppColors.WARNING
                terminal.append_line("[STOPPED] AIO Statistics script terminated by user.")
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
            ft.Text("1. Create the column headers for your new Excel file.", weight=ft.FontWeight.BOLD, size=13),
            ft.Row([new_column_input, add_column_btn, reset_tags_btn], spacing=10),
            columns_hint,
            columns_row,
            ft.Text("2. Add the tags present in your data files and pick the column each one goes into.",
                    weight=ft.FontWeight.BOLD, size=13),
            ft.Text("Example: tags F and M ➔ column Gender give one 'Gender' column with F/M values.",
                    size=12, color=AppColors.TEXT_MUTED),
            ft.Row([tag_code_input, column_dropdown, add_tag_btn], spacing=10),
            tags_list_container,
            ft.Row([group_trials_switch], spacing=15),
        ], spacing=15),
        title="Dynamic File Tagging & Grouping",
        icon=ft.Icons.LABEL
    )

    timepoint_card = create_card(
        ft.Column([
            ft.Text(
                "Week codes in file names (e.g. 44W) fill a 'Timepoint' column automatically. "
                "Set when your experiments start and how often they repeat.",
                size=12, color=AppColors.TEXT_MUTED
            ),
            ft.Row([start_week_input, interval_input], spacing=10),
            schedule_preview,
        ], spacing=15),
        title="Timepoint Schedule",
        icon=ft.Icons.SCHEDULE
    )

    return ft.ListView([
        ft.Text("Descriptive Statistics - All In One", size=22, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN),
        status_text,
        ft.Container(height=10),
        folder_card,
        tagging_card,
        timepoint_card,
        ft.Row([run_btn, stop_btn], spacing=10),
        progress_bar,
        terminal.get_control()
    ], spacing=15, padding=20)

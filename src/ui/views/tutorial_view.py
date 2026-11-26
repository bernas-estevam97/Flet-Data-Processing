import flet as ft
from ui.theme import AppColors, create_card, button_hover_style
from filter_settings import settings_rows, HEIGHT_CUTOFF_X, mm

def build_tutorial_view(page: ft.Page) -> ft.Control:
    header_section = ft.Column([
        ft.Row([
            ft.Icon(ft.Icons.ANALYTICS, size=36, color=AppColors.PRIMARY),
            ft.Text("MotoRater Data Processing Guide", size=26, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN),
        ], alignment=ft.MainAxisAlignment.START, spacing=12),
        ft.Text(
            "Welcome to the MotoRater automated data processing suite! This application accelerates your kinematic data analysis by bulk-filtering raw Excel files, extracting key statistical metrics, and compiling experiment-wide summaries.",
            color=AppColors.TEXT_MUTED, size=15
        ),
    ], spacing=10)

    step1_card = create_card(
        ft.Column([
            ft.ListTile(
                leading=ft.Icon(ft.Icons.FILTER_ALT, size=28, color=AppColors.PRIMARY),
                title=ft.Text("Step 1: Raw Data Filtering", weight=ft.FontWeight.BOLD, size=18, color=AppColors.TEXT_MAIN),
                subtitle=ft.Text("Bulk-clean and normalize raw kinematics Excel files.", color=AppColors.TEXT_MUTED)
            ),
            ft.Divider(color=AppColors.BORDER),
            ft.Markdown(
                """
1. **Select Data Folder**: Choose the folder containing your raw MotoRater `.xlsx` files.
2. **Select Output Folder (Optional)**: Choose where cleaned `_filtered.xlsx` files will be saved (defaults to input folder).
3. **Experiment Setup**:
   - **Experiment Type**: Select Groundwalk, Gridwalk, Beamwalk, or Swimming.
   - **Animal Species**: Select *Mus Musculus* or *Acomys*. Also sets the tracking jump limit (see **How Filtering Cleans Your Data** below).
   - **Cutoff Starts Where?**: The marker that marks the start of movement (Tail Tip, Tail Center, Tail Base, or Both Paws). Movement ends when the nose reaches its exit position.
4. **Floor & Height Reference**:
   - **Floor Reference**: *Auto* (recommended) measures the floor in each file from the resting hind toe, so heights stay correct when the setup moves between sessions. *Fixed* uses the stored constant for the selected species, experiment and camera.
   - **Camera Settings**: Old vs New camera setup. Shown only with a *Fixed* floor, where it selects the stored constant.
   - **Hind Paw Height Cutoff**: Blanks height, clearance and drag values once the right hind toe reaches X = """ + mm(HEIGHT_CUTOFF_X) + """.
5. **Paw Swing Detection**:
   - **Swing Speed Threshold (m/s)**: Paw speed and acceleration are kept only for frames where that paw moves faster than this value (swing phase). The recommended value fills in when you pick the experiment or species (Groundwalk/Gridwalk 0.1, Beamwalk 0.03). Use the reset button to restore it. Enter **0** to keep every frame.
6. **Output**:
   - **Keep Positions Sheet**: Copies the raw `Positions (used)` sheet into each filtered file. Turn off for about 2x faster filtering when you don't need the positions.
   - Kinematics are rebuilt from the `Positions (used)` sheet, and quality-control columns (`QC Tracked Frames (%)`, `QC Hind Ahead of Front (%)`, `QC Step Length SD`) are added to every file.
7. **Advanced Filter Settings**: Expand this card to see the fixed v2 values used to clean the data. They are read-only (see **How Filtering Cleans Your Data** below).
8. **Run**: Click **Run Data Filtering**. Files are processed in the background with live log feedback (in parallel or one at a time, see **Sidebar Controls** below). Already filtered files will automatically skip to save time.
                """,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
            )
        ], spacing=10)
    )

    mus, aco = settings_rows("0"), settings_rows("1")
    settings_table = "| Group | Setting | Mus | Acomys | What it does |\n|---|---|---|---|---|\n" + "\n".join(
        f"| {g} | {name} | {v0} | {v1} | {meaning} |"
        for (g, name, v0, meaning), (_, _, v1, _) in zip(mus, aco))

    pipeline_card = create_card(
        ft.Column([
            ft.ListTile(
                leading=ft.Icon(ft.Icons.CLEANING_SERVICES, size=28, color=AppColors.PRIMARY),
                title=ft.Text("How Filtering Cleans Your Data", weight=ft.FontWeight.BOLD, size=18, color=AppColors.TEXT_MAIN),
                subtitle=ft.Text("Every step applied to each file, in order, and the fixed values behind it.", color=AppColors.TEXT_MUTED)
            ),
            ft.Divider(color=AppColors.BORDER),
            ft.Markdown(
                """
1. **Movement window**: Starts when the selected start marker first moves away from its parked position. Ends at the first frame the nose reaches its exit position, or stops being tracked near the exit.
2. **Placeholders removed**: When the tracker loses a marker it repeats the last position. Frames where a marker's X and Y repeat exactly are removed from every measurement.
3. **Implausible positions removed**:
   - **Body checks** remove the whole frame: nose behind a hind paw, hind paw well ahead of the front paw (label swap), or body length far from the session median.
   - **Jumps** remove one marker in one frame: it moved further than a paw can in one frame.
   - **Spikes** remove one-frame out-and-back jitter (common on the beam). Tail markers are skipped because the tail really whips that fast.
4. **Kinematics rebuilt**: Every measurement with a known formula (heights, distances, angles, paw speed and acceleration) is recomputed from the cleaned `Positions (used)` sheet. Paw speed and acceleration use a Savitzky-Golay derivative (window 5, order 2). Columns without a formula are kept from the `Kinematics` sheet and listed in the log.
5. **Floor and heights**: Heights are measured from the floor (Auto or Fixed). The optional height cutoff blanks heights once the right hind toe reaches X = """ + mm(HEIGHT_CUTOFF_X) + """.
6. **Swing only**: Paw speed and acceleration are kept only above the swing speed threshold.
7. **Quality control**: `QC` columns are added, and the log flags files that need checking ("CHECK THIS VIDEO", low tracking).
8. **Statistics**: Mean, Std, Median, Min, Max, IQR, P5-P95 Range and Time Duration are added below the data.

**Fixed settings** (also shown in the Filtering tab under *Advanced Filter Settings*):

""" + settings_table + """

These values were tuned on about 800 files across groundwalk, gridwalk and beam sessions. Acomys values other than the jump limit are provisional until more Acomys sessions are tested. Each file's log entry lists what was removed and why.
                """,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
            )
        ], spacing=10)
    )

    step2_card = create_card(
        ft.Column([
            ft.ListTile(
                leading=ft.Icon(ft.Icons.BAR_CHART, size=28, color=ft.Colors.PURPLE_400),
                title=ft.Text("Step 2: Descriptive Statistics", weight=ft.FontWeight.BOLD, size=18, color=AppColors.TEXT_MAIN),
                subtitle=ft.Text("Compile summary metrics across processed datasets.", color=AppColors.TEXT_MUTED)
            ),
            ft.Divider(color=AppColors.BORDER),
            ft.Markdown(
                """
1. **Select Filtered Data Folder**: Choose the directory containing your `_filtered.xlsx` files from Step 1.
2. **Select Output Folder (Optional)**: Choose destination for the summary statistics workbook.
   - **Output file name (optional)**: Name the workbook. Leave empty for `EXPERIMENT_descriptive_statistics.xlsx`.
   - Every sheet in the output is sorted by `Ids` (natural order, so M2 comes before M10).
3. **Experiment Name**: Label your experiment type for file naming.
4. **Group Trials (Calculate Means)**: 
   - **Enabled**: Automatically detects trial numbers (e.g. `_1`, `_2`) and computes subject averages.
   - **Disabled**: Preserves each trial row individually without subject averaging.
5. **Run**: Click **Run Descriptive Statistics** to generate an Excel workbook with sheets for `Mean`, `Std`, `Median`, `Min`, `Max`, `IQR`, `P5-P95 Range`, and `Time Duration`.
   - **IQR** (Q3 − Q1): spread of the middle 50% of frames.
   - **P5-P95 Range** (P95 − P5): amplitude of the middle 90% of frames, e.g. range of motion or swing height.
   - Both are in the column's own units, valid for negative and near-zero values (floor-referenced heights, Vx/Vy, accelerations), and not driven by a single extreme frame or by trial length. They replace `Max_Normalized_Mean` and `CV`, which divide by the max or mean and break down for such data. Files filtered before this change still carry the old rows: filter them again to get the new sheets.
                """,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
            )
        ], spacing=10)
    )

    step3_card = create_card(
        ft.Column([
            ft.ListTile(
                leading=ft.Icon(ft.Icons.AUTO_AWESOME, size=28, color=AppColors.ACCENT),
                title=ft.Text("Step 3: Statistics All-In-One (AIO Tagging)", weight=ft.FontWeight.BOLD, size=18, color=AppColors.TEXT_MAIN),
                subtitle=ft.Text("Parse custom filename tags and group datasets dynamically.", color=AppColors.TEXT_MUTED)
            ),
            ft.Divider(color=AppColors.BORDER),
            ft.Markdown(
                """
1. **Create Column Headers**: Type a name in "New column header name" and click **Add Column** (or press Enter). Each header becomes a new column in the output Excel file, e.g. `Experimental Group`, `Gender`, `Test`. Click the ✕ on a header to remove it and its tags.
2. **Add File Tags**: Type a tag present in your data files in "Tag present in your data files", pick the column it goes into from the **Goes into column** dropdown, then click **Add Tag**. The cell value is the tag itself.
   - `WT` ➔ `Experimental Group`, `TG` ➔ `Experimental Group`
   - `F` ➔ `Gender`, `M` ➔ `Gender`
   - `BEAM` ➔ `Test`

   Tags sharing a column fill the same column. Columns appear in the order you created them.
3. **Timepoint Schedule**: Week parts like `44W` fill a `Timepoint` column automatically. Set **First timepoint (week)** and **Weeks between timepoints** to match your protocol. The default (start `4W`, every `4W`) gives `44W` ➔ `11`; start `2W`, every `3W` gives `2W` ➔ `1`, `5W` ➔ `2`, `8W` ➔ `3`. Weeks off the schedule show a warning in the terminal.
4. **Result**: `2199_1R_44W_01_BEAM_WT_F_out_processed_filtered.xlsx` becomes the row:

| Ids | Experimental Group | Gender | Test | Timepoint | ...stats |
|---|---|---|---|---|---|
| 2199_1R | WT | F | BEAM | 11 | ... |

5. **Select Filtered Folder**: Choose the folder containing your `_filtered.xlsx` files. Optionally type an **Output file name**; leave it empty for `TAGGED_EXPERIMENT_AIO_descriptive_statistics.xlsx`. Rows are sorted by `Ids`.
6. **Group Trials by ID & Tags**: Averages trials (`_01`, `_02`, ...) that share the same Id, tags and timepoint into one row.
7. **Run**: Click **Run Descriptive AIO Statistics** to export tagged summary workbooks.
                """,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
            )
        ], spacing=10)
    )

    step4_card = create_card(
        ft.Column([
            ft.ListTile(
                leading=ft.Icon(ft.Icons.CALL_MERGE, size=28, color=ft.Colors.ORANGE_400),
                title=ft.Text("Step 4: Excel File Merger (Optional)", weight=ft.FontWeight.BOLD, size=18, color=AppColors.TEXT_MAIN),
                subtitle=ft.Text("Merge multiple identically structured Excel workbooks.", color=AppColors.TEXT_MUTED)
            ),
            ft.Divider(color=AppColors.BORDER),
            ft.Markdown(
                """
1. **Select Excel Files**: Pick two or more `.xlsx` files with matching sheet structures.
2. **Set Output Path & Filename**: Choose output directory and name (e.g. `Merged_Data.xlsx`).
3. **Run**: Click **Run File Merge** to vertically combine all sheets into a single master document. Rows are sorted by `Ids` (natural order, so M2 comes before M10).
                """,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
            )
        ], spacing=10)
    )

    sidebar_controls_card = create_card(
        ft.Column([
            ft.ListTile(
                leading=ft.Icon(ft.Icons.TUNE, size=28, color=AppColors.PRIMARY),
                title=ft.Text("Sidebar Controls", weight=ft.FontWeight.BOLD, size=18, color=AppColors.TEXT_MAIN),
                subtitle=ft.Text("Processing speed, stopping tasks and theme.", color=AppColors.TEXT_MUTED)
            ),
            ft.Divider(color=AppColors.BORDER),
            ft.Markdown(
                """
- **Parallel / Sequential switch**:
   - **Parallel (ON)**: Processes several files at once using most CPU cores. Much faster, but the computer may feel slow while a task runs.
   - **Sequential (OFF)**: Processes one file at a time. Slower, but light on low-end PCs or while you keep working.
   - The setting applies to the next task you start, not to a task already running.
- **Force Stop**: The red stop button becomes active while a task runs. Click it to stop all running tasks at once. The badge below it shows how many tasks are active.
- **Theme**: Switches between light and dark mode.
                """,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
            )
        ], spacing=10)
    )

    admin_support_card = create_card(
        ft.Column([
            ft.ListTile(
                leading=ft.Icon(ft.Icons.HELP_OUTLINE, size=28, color=AppColors.PRIMARY),
                title=ft.Text("Need Help or Technical Support?", weight=ft.FontWeight.BOLD, size=18, color=AppColors.TEXT_MAIN),
                subtitle=ft.Text("Direct assistance and custom setup options.", color=AppColors.TEXT_MUTED)
            ),
            ft.Divider(color=AppColors.BORDER),
            ft.Text(
                "If you have any questions about operating the data pipeline, need custom subtraction/offset calibration parameters added, or encounter issues processing your experimental files, please contact me through my website for direct assistance.",
                color=AppColors.TEXT_MUTED, size=14
            ),
            ft.OutlinedButton(
                "bernas-estevam97.github.io",
                icon=ft.Icons.OPEN_IN_NEW,
                url="https://bernas-estevam97.github.io/",
                tooltip="Open in your browser",
                style=button_hover_style
            )
        ], spacing=10)
    )

    # Column, not ListView: ListView builds cards lazily and re-estimates the page height while scrolling past
    # cards of very different heights, so the scrollbar thumb keeps resizing. 8 cards: laying out all is cheap.
    return ft.Column([
        ft.Container(ft.Column([
            header_section,
            ft.Container(height=5),
            step1_card,
            pipeline_card,
            step2_card,
            step3_card,
            step4_card,
            sidebar_controls_card,
            admin_support_card
        ], spacing=15), padding=20)
    ], scroll=ft.ScrollMode.AUTO, expand=True)

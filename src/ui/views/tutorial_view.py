import flet as ft
from ui.theme import AppColors, create_card, button_hover_style

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
3. **Configure Experiment Settings**:
   - **Cutoff Location**: Choose start trigger location (Tail Tip, Tail Center, Tail Base, or Both Paws).
   - **Animal Species**: Select *Mus Musculus* or *Acomys*.
   - **Experiment Type**: Select Groundwalk, Gridwalk, Beamwalk, or Swimming.
   - **Camera Settings**: Select Old vs New calibration settings.
   - **Hind Paw Height Cutoff**: Enable to truncate kinematics past hind paw touch threshold.
   - **Keep Positions Sheet**: Copies the raw `Positions (used)` sheet into each filtered file. Turn off for about 2x faster filtering when you don't need the positions.
4. **Run**: Click **Run Data Filtering**. Files are processed in the background with live log feedback (in parallel or one at a time, see **Sidebar Controls** below). Already filtered files will automatically skip to save time.
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
3. **Experiment Name**: Label your experiment type for file naming.
4. **Group Trials (Calculate Means)**: 
   - **Enabled**: Automatically detects trial numbers (e.g. `_1`, `_2`) and computes subject averages.
   - **Disabled**: Preserves each trial row individually without subject averaging.
5. **Run**: Click **Run Descriptive Statistics** to generate an Excel workbook with sheets for `Mean`, `Std`, `Median`, `Min`, `Max`, `Max_Normalized_Mean`, `CV`, and `Time Duration`.
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
1. **Define Filename Tags**: Each tag maps a code from your file names to an Excel **column**. The column name is what you type in "Column"; the cell value is the code itself.
   - `WT` ➔ `Experimental Group`, `TG` ➔ `Experimental Group`
   - `F` ➔ `Gender`, `M` ➔ `Gender`
   - `BEAM` ➔ `Test`

   Tags sharing a column name fill the same column. Columns appear in the order you add the tags.
2. **Timepoint (automatic)**: Week parts like `44W` become a `Timepoint` column (weeks ÷ 4, so `44W` ➔ `11`). No tag needed.
3. **Result**: `2199_1R_44W_01_BEAM_WT_F_out_processed_filtered.xlsx` becomes the row:

| Ids | Experimental Group | Gender | Test | Timepoint | ...stats |
|---|---|---|---|---|---|
| 2199_1R | WT | F | BEAM | 11 | ... |

4. **Select Filtered Folder**: Choose the folder containing your `_filtered.xlsx` files.
5. **Group Trials by ID & Tags**: Averages trials (`_01`, `_02`, ...) that share the same Id, tags and timepoint into one row.
6. **Run**: Click **Run Descriptive AIO Statistics** to export tagged summary workbooks.
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
3. **Run**: Click **Run File Merge** to vertically combine all sheets into a single master document.
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

    return ft.ListView([
        header_section,
        ft.Container(height=5),
        step1_card,
        step2_card,
        step3_card,
        step4_card,
        sidebar_controls_card,
        admin_support_card
    ], spacing=15, padding=20)

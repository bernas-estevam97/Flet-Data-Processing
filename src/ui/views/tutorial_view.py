import flet as ft
from ui.theme import AppColors, create_card

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
4. **Run**: Click **Run Data Filtering**. Multi-core processing executes in the background with live log feedback. Already filtered files will automatically skip to save time.
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
1. **Define Filename Tags**: Add tag codes used in your file names and their meanings (e.g. Code: `F` ➔ Meaning: `Female`, Code: `WT` ➔ Meaning: `Wild Type`).
2. **Select Filtered Folder**: Choose the folder containing your `_filtered.xlsx` files.
3. **Group Trials by ID & Tags**: Automatically groups subjects by base ID and matched experimental tags.
4. **Run**: Click **Run Descriptive AIO Statistics** to export tagged summary workbooks.
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

    admin_support_card = create_card(
        ft.Column([
            ft.ListTile(
                leading=ft.Icon(ft.Icons.HELP_OUTLINE, size=28, color=AppColors.PRIMARY),
                title=ft.Text("Need Help or Technical Support?", weight=ft.FontWeight.BOLD, size=18, color=AppColors.TEXT_MAIN),
                subtitle=ft.Text("Direct assistance and custom setup options.", color=AppColors.TEXT_MUTED)
            ),
            ft.Divider(color=AppColors.BORDER),
            ft.Text(
                "If you have any questions about operating the data pipeline, need custom subtraction/offset calibration parameters added, or encounter issues processing your experimental files, please contact your system administrator for direct assistance.",
                color=AppColors.TEXT_MUTED, size=14
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
        admin_support_card
    ], spacing=15, padding=20)

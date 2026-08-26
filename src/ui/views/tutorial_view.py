import flet as ft
from ui.theme import AppColors, create_card

def build_tutorial_view(page: ft.Page) -> ft.Control:
    header_section = ft.Column([
        ft.Row([
            ft.Icon(ft.Icons.ANALYTICS, size=40, color=AppColors.PRIMARY),
            ft.Text("MotoRater Data Pipeline", size=28, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_MAIN),
        ], alignment=ft.MainAxisAlignment.START, spacing=12),
        ft.Text(
            "Welcome to the MotoRater automated data processing suite. This tool is designed to take your raw experimental data, apply rigorous filtering criteria, and generate clean, descriptive statistics.",
            color=AppColors.TEXT_MUTED, size=15
        ),
    ], spacing=10)

    step1_card = create_card(
        ft.Column([
            ft.ListTile(
                leading=ft.Icon(ft.Icons.FILTER_ALT, size=28, color=AppColors.PRIMARY),
                title=ft.Text("Step 1: Data Filtering", weight=ft.FontWeight.BOLD, size=18, color=AppColors.TEXT_MAIN),
                subtitle=ft.Text("Process raw .xlsx files in bulk using parallel processing.", color=AppColors.TEXT_MUTED)
            ),
            ft.Divider(color=AppColors.BORDER),
            ft.Markdown(
                """
* **Select Data Folder:** Choose the directory containing your raw `.xlsx` files.
* **Select Output Folder (Optional):** Define where the cleaned files will be saved. Defaults to input folder.
* **Set Parameters:** Select your Cutoff, Animal Species, Experiment Type, Camera Settings, and Hind Paw Height Cutoff switch.
* **Run:** Click **Run Data Filtering**. The system processes files in parallel with live status logging.
                """,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
            )
        ], spacing=10),
        title="Step 1: Data Filtering",
        icon=ft.Icons.FILTER_ALT
    )

    step2_card = create_card(
        ft.Column([
            ft.ListTile(
                leading=ft.Icon(ft.Icons.BAR_CHART, size=28, color=ft.Colors.PURPLE_400),
                title=ft.Text("Step 2: Descriptive Statistics", weight=ft.FontWeight.BOLD, size=18, color=AppColors.TEXT_MAIN),
                subtitle=ft.Text("Generate summary statistics from your filtered datasets.", color=AppColors.TEXT_MUTED)
            ),
            ft.Divider(color=AppColors.BORDER),
            ft.Markdown(
                """
* **Select Filtered Data Folder:** Choose the directory containing the `.xlsx` files processed in Step 1.
* **Select Output Folder (Optional):** Choose a destination for your final statistics workbook.
* **Trial Grouping:** Toggle whether trials (`_1`, `_2`) are averaged per subject or preserved individually.
* **Run:** Click **Run Descriptive Statistics** to compile summary tables (Mean, Std, Median, Min, Max, Max_Normalized_Mean, CV).
                """,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
            )
        ], spacing=10),
        title="Step 2: Descriptive Statistics",
        icon=ft.Icons.BAR_CHART
    )

    step3_card = create_card(
        ft.Column([
            ft.ListTile(
                leading=ft.Icon(ft.Icons.AUTO_AWESOME, size=28, color=AppColors.ACCENT),
                title=ft.Text("Step 3: Descriptive AIO Statistics", weight=ft.FontWeight.BOLD, size=18, color=AppColors.TEXT_MAIN),
                subtitle=ft.Text("Extract experimental tags and generate tagged summary statistics.", color=AppColors.TEXT_MUTED)
            ),
            ft.Divider(color=AppColors.BORDER),
            ft.Markdown(
                """
* **Dynamic File Tagging:** Define filename tag codes and meanings (e.g. `F` ➔ `Female`, `WT` ➔ `Wild Type`).
* **Select Filtered Data Folder:** Choose the directory containing `.xlsx` files.
* **Trial Grouping:** Toggle grouping by Subject ID and Identified Tags.
* **Run:** Click **Run Descriptive AIO Statistics** to generate tagged datasets.
                """,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
            )
        ], spacing=10),
        title="Step 3: Descriptive AIO Statistics",
        icon=ft.Icons.AUTO_AWESOME
    )

    step4_card = create_card(
        ft.Column([
            ft.ListTile(
                leading=ft.Icon(ft.Icons.CALL_MERGE, size=28, color=ft.Colors.ORANGE_400),
                title=ft.Text("Step 4: Merge Data (Optional)", weight=ft.FontWeight.BOLD, size=18, color=AppColors.TEXT_MAIN),
                subtitle=ft.Text("Combine multiple identically structured Excel files into a single master workbook.", color=AppColors.TEXT_MUTED)
            ),
            ft.Divider(color=AppColors.BORDER),
            ft.Markdown(
                """
* **Select Excel Files:** Choose two or more `.xlsx` files to combine.
* **Select Output Folder & Filename:** Define destination directory and filename (e.g., `Combined_Results.xlsx`).
* **Run:** Click **Run File Merge** to vertically merge matching sheets into a single Excel file.
                """,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
            )
        ], spacing=10),
        title="Step 4: Merge Data",
        icon=ft.Icons.MERGE_TYPE
    )

    return ft.ListView([
        header_section,
        ft.Container(height=10),
        step1_card,
        step2_card,
        step3_card,
        step4_card
    ], spacing=15, padding=20)

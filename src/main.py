import flet as ft
import subprocess # Useful for running external scripts

def main(page: ft.Page):
    # 1. App Configuration & Custom Icon
    page.title = "My Script Manager"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 600
    page.window_height = 400
    
    # The icon path is relative to the 'assets' folder you define in ft.app()
    # If your icon is at assets/icon.png, use "/icon.png"
    # Note: This works for the window icon when compiled or running as a desktop app.
    page.window_icon = "/new-icon.png" 

    # 2. Logic to run your scripts
    def run_script_one(e):
        try:
            # Replace 'script1.py' with your actual filename
            # Use path relative to main.py or absolute path
            subprocess.run(["python", "src/script1.py"], check=True)
            status_text.value = "Script 1 executed successfully!"
        except Exception as err:
            status_text.value = f"Error: {err}"
        page.update()

    # 3. UI Components
    status_text = ft.Text("System Ready", color=ft.Colors.BLUE_GREY_400)

    page.add(
        ft.Column(
            [
                ft.Text("Script Controller", size=30, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Button("Run Data Processor", icon=ft.Icons.PLAY_ARROW, on_click=run_script_one),
                ft.Button("Run Backup Script", icon=ft.Icons.BACKUP),
                status_text,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )

# 4. Critical: Pointing to the Assets folder
# assets_dir specifies where your images/icons are located
if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
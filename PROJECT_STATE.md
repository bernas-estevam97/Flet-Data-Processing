# MotoRater Data Processing App - Project State & Cold Memory Checkpoint

> **Date Updated**: October 19, 2026
> **Status**: Fully operational
> **Environment**: Python 3.10+ managed by `uv` (`.venv`, `uv.lock`)
> **Framework**: Flet 1.0.4 (Desktop UI) | Pandas | rustpy-xlsxwriter

---

## 1. Project Overview

The **MotoRater Data Processing & Analysis Application** is a modular desktop GUI app built with Python and Flet. It processes kinematic data output from MotoRater experimental hardware by bulk-filtering raw Excel workbooks, extracting descriptive statistical metrics (Mean, Std, Median, Min, Max, Max_Normalized_Mean, CV, Time Duration), supporting dynamic filename tag parsing, and merging multi-sheet Excel files.

---

## 2. Directory & File Structure

```
Flet-Data-Processing/
├── pyproject.toml              # Dependencies + [tool.flet] build config (app path = src, icon = assets/icon.ico)
├── uv.lock                     # Locked dependency versions (git-ignored)
├── requirements.txt            # pip-style dependency list
├── commands.txt                # Setup / run / build commands (git-ignored)
├── PROJECT_STATE.md            # This file
├── src/
│   ├── main.py                 # Entry point: layout, NavigationRail, sidebar controls, --run-task dispatch
│   ├── process_manager.py      # Task launching (subprocess or in-process thread), force stop, worker_count()
│   ├── ex_filtering.py         # Raw data filtering (parallel pool, height cutoff, optional Positions sheet)
│   ├── desc_analysis.py        # Descriptive statistics (subject trial grouping, metric calculations)
│   ├── desc_analysis_aio.py    # Tagged statistics (filename tag parser, Timepoint from week tags)
│   ├── merge_excel.py          # Vertical merge of identically structured Excel files
│   ├── assets/                 # icon.ico, icon.png, splash_android.png (+ *_old / *_default variants)
│   ├── ui/
│   │   ├── theme.py            # AppColors semantic tokens, button_hover_style, create_card()
│   │   ├── terminal.py         # Live log terminal with text selection & Copy Logs button
│   │   └── views/
│   │       ├── tutorial_view.py  # In-app guide (Steps 1-4, Sidebar Controls, help card with website link)
│   │       ├── filtering_view.py # Filtering UI (parameter dropdowns, Height Cutoff + Keep Positions switches)
│   │       ├── stats_view.py     # Descriptive statistics UI (grouping switch)
│   │       ├── stats_aio_view.py # AIO statistics UI (tag manager)
│   │       └── merge_view.py     # Excel merger UI (selected files list with per-file remove)
│   └── legacy_v1/              # Archived monolithic V1 app, kept for reference
```

---

## 3. Key Features & Technical Solutions

### A. Modular Flet Architecture (Flet 1.0.4)
- All UI lives in `src/ui/views/`; `main.py` only builds the shell (NavigationRail, sidebar, theme).
- Upgrading to Flet 1.0.4 fixed a stray `flet` folder being created in the user's Documents folder.
- Keep `flet-cli`, `flet-desktop` and `flet-web` (dev group) on the same version as `flet`.

### B. Theme & UX
- Material 3 adaptive tokens in `AppColors` for contrast in Light and Dark themes.
- Pointer cursor on hover: reuse `button_hover_style` (`ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK)`) from `ui/theme.py` for any new button. NavigationRail destinations are wrapped in `ft.GestureDetector`.
- Reset buttons (`ft.Icons.RESTART_ALT`) beside path fields; merge view lists each selected file with an `[X]` remove button.
- Terminal logs are in `ft.SelectionArea`; Copy Logs uses `await ft.Clipboard().set(...)`.

### C. Task Execution Model (`process_manager.py`)
- `start_task(script, args)` picks how to run a processing script:
  - **Dev run / `flet pack` exe**: spawns a child process. In a PyInstaller exe, `main.py` relaunches itself with `--run-task <script>` (`RUN_TASK_FLAG`) and dispatches to `task_main(script)`.
  - **`flet build` app**: Python is embedded in the Flutter exe and cannot spawn processes, so the script runs in a thread (`InProcessTask`) that mimics `asyncio.subprocess.Process`. Its pool falls back to `ThreadPoolExecutor`, which is much slower (about 5x on filtering).
- `can_spawn_processes()` detects which mode is possible.
- Windows children start with `BELOW_NORMAL_PRIORITY_CLASS` (inherited by pool workers) so the PC stays responsive.
- POSIX children start with `start_new_session=True`, so Force Stop's `os.killpg` kills the task tree and not the GUI (fixed Linux/macOS bug).
- Force Stop: Windows uses `taskkill /F /T /PID`; in-process tasks stop at their next print.

### D. Parallel / Sequential Mode
- Sidebar switch in `main.py` sets env var `MOTORATER_SEQUENTIAL` (`SEQUENTIAL_ENV`); child processes inherit it.
- `worker_count(n_tasks)` is used by `ex_filtering.py`, `desc_analysis.py` and `desc_analysis_aio.py`:
  - Sequential: 1 worker.
  - Parallel: `cores - 2` (or `cores - 1` when 4 cores or fewer), never more than the number of files.
- The setting applies to the next task started, not to a running task.
- This replaces the older `total_cores - 4` tuning for external drives.

### E. Fast Excel Writing in Filtering (`ex_filtering.py`)
- Output is written with `rustpy_xlsxwriter.write_worksheets(...)` (Rust-based) from row dicts built by `records(df)`. About 4-7x faster than `DataFrame.to_excel`.
- Output values match the old pandas writer, except tiny differences at the 17th significant digit.
- **Keep Positions Sheet** switch (`keep_positions` "yes"/"no", last CLI argument): when off, the raw `Positions (used)` sheet is skipped, making filtering about 2x faster.
- `flet pack` needs `--pyinstaller-build-args="--copy-metadata=rustpy-xlsxwriter"`, otherwise the packed exe crashes on import (see `commands.txt`).
- Remaining floor: reading is about 0.5 s per file. Bigger gains would need a different output format (CSV/Parquet), which would change the downstream pipeline.
- Statistics scripts still write with pandas + `xlsxwriter`; merge uses `openpyxl`.

### F. Excel Reading & Lock Files
- Readers try engines in order `calamine` ➔ `openpyxl` ➔ default.
- Excel lock files (`~$...xlsx`) are excluded when listing files and skipped in the per-file extractors.
- Already filtered files (`_filtered.xlsx`) are skipped by filtering.

### G. AIO Tagging (`desc_analysis_aio.py`)
- Each user tag maps a filename code to a column (e.g. `WT` ➔ `Experimental Group`, `F` ➔ `Gender`).
- Week parts like `44W` become a `Timepoint` column (weeks / 4).
- Optional grouping averages trials sharing Id, tags and timepoint.

### H. Tutorial Page
- `tutorial_view.py` must be updated whenever a user-facing feature is added or changed.
- The help card links to https://bernas-estevam97.github.io/ (OutlinedButton with `url=`).

---

## 4. Execution & Build Reference Commands

Run from the project root. Full details in `commands.txt`.

```powershell
uv sync                          # setup
uv run flet run src              # run in development

# Windows app folder (in-process thread mode, slower parallel processing)
uv run flet build windows --project MotoRater_Data_Processing --compile-app --compile-packages

# PyInstaller build (full multiprocessing); -D for one-folder output
uv run flet pack src/main.py -D --name MotoRater_Data_Processing --icon src/assets/icon.ico --add-data "src/assets;assets" --pyinstaller-build-args="--copy-metadata=rustpy-xlsxwriter"
```

Update dependencies with `uv add` (not by hand) so `pyproject.toml` and `uv.lock` stay in sync.

---

## 5. Notes for Future Agents / Continuation
- Entry point: `src/main.py`. Processing scripts live directly in `src/` and expose `main(argv)`; register new ones in `task_main()` with a static import so PyInstaller bundles them.
- New pool-based scripts should use `worker_count()` and fall back to `ThreadPoolExecutor` when `can_spawn_processes()` is False.
- `ex_filtering.py`, `desc_analysis.py` and `desc_analysis_aio.py` also run standalone with interactive prompts when no arguments are given.
- Keep the tutorial page and this file in sync with feature changes.

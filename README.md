# MotoRater Data Processing

A desktop app that turns raw **MotoRater** kinematics exports (`.xlsx`) into clean, analysis-ready Excel summaries. You don't need to write any code.

You point it at a folder of recordings. It trims each trial to the real movement, calibrates the values and calculates statistics. It then combines everything into one workbook per experiment.

Built with Python, [Flet](https://flet.dev) and pandas.

---

## What it does

The app has four tools, available from the sidebar:

| Tool | Input | Output |
|---|---|---|
| **1. Data Filtering** | Folder of raw MotoRater `.xlsx` files | One `*_filtered.xlsx` per file: trimmed, calibrated, with per-file statistics |
| **2. Statistics** | Folder of `*_filtered.xlsx` files | One summary workbook (one sheet per statistic, one row per subject or trial) |
| **3. Statistics – AIO** | Folder of `*_filtered.xlsx` files, your filename tags and your timepoint schedule | Same summary, with extra columns (group, gender, test, timepoint) parsed from file names |
| **4. Merge Data** | Two or more Excel files with the same sheets | A single workbook where each sheet is stacked from all files and sorted by ID |

A built-in **Tutorial** page explains every option in detail.

### 1. Data Filtering

For each raw file (sheets `Positions (used)` and `Kinematics`), the app:

- **Trims the trial.** It finds the frame where the animal starts moving, based on the cutoff point you choose: tail tip, tail center, tail base or both hind paws. It finds where movement stops from the nose position.
- **Rebuilds the kinematics.** It recalculates heights, distances, joint angles and paw speeds/accelerations (Savitzky-Golay) from the `Positions (used)` sheet. The original `Kinematics` sheet has outlier filtering that cuts swing peaks. Columns are matched by name, not position.
- **Measures heights from the floor.** *Auto* (default) finds the floor in each file from the resting hind toe. *Fixed* uses the stored constant for the species (*Mus musculus* or *Acomys*), the test (groundwalk, beamwalk, gridwalk or swimming) and the camera setup (old or new). The camera setting appears only with a *Fixed* floor.
- **Applies the hind paw cutoff (optional).** It blanks out height values once the right hind toe reaches X = −20 mm (same for both camera setups).
- **Keeps swing frames only.** Paw speed and acceleration are kept only where the paw moves faster than the swing threshold (default 0.1 m/s; 0.03 m/s for beamwalk; 0 keeps every frame).
- **Adds quality-control columns.** Tracked frames (%), hind paw ahead of front paw (%) and step length SD flag tracking problems.
- **Removes bad positions.** Tracker placeholders (frozen markers), tracking jumps, one-frame jitter spikes and frames that fail body checks (nose behind a hind paw, hind/front label swaps, implausible body length) are removed before any measurement. The fixed values are shown, read-only, under *Advanced Filter Settings* in the Filtering tab and explained in the Tutorial. They live in `src/filter_settings.py`.
- **Calculates statistics.** It appends Mean, Std, Median, Min, Max, IQR (Q3 − Q1), P5-P95 Range (P95 − P5) and Time Duration. IQR and P5-P95 Range replace Max-Normalized Mean and CV, which divide by the max or mean and are not valid for signed or near-zero data such as floor-referenced heights and velocities.

Files are processed in parallel on all CPU cores. If an output file already exists, the app skips it, so you can safely re-run an interrupted batch.

### 2. Statistics

This tool collects the statistics from every filtered file into one Excel workbook. It creates one sheet per statistic (`Mean`, `Std`, `Median`, `Min`, `Max`, `IQR`, `P5-P95 Range`, `Time Duration`). Files filtered before the IQR/P5-P95 change still carry the old rows; filter them again to get the new sheets. You can average the repeated trials of each subject (`_1`, `_2`, …) or keep each trial as its own row.

Both statistics tools sort every sheet by `Ids` (natural order, so M2 comes before M10). Both statistics tools have an optional **Output file name** field. Leave it empty to use the default name. The app adds `.xlsx` and removes characters Windows does not allow in file names.

### 3. Statistics – AIO (All-In-One)

This tool does the same as Statistics. It also reads **tags** from the file names and turns them into columns. Set them up in two steps:

1. **Create column headers** for the new Excel file, for example *Experimental Group*, *Gender*, *Test*.
2. **Add the tags present in your data files** and pick the column each tag goes into from a dropdown:
   - `WT`, `TG` → *Experimental Group*
   - `F`, `M` → *Gender*
   - `BEAM` → *Test*

The tag itself becomes the cell value. Columns appear in the order you created them.

Week codes such as `44W` automatically become a **Timepoint** column. In **Timepoint Schedule**, set the week of your first experiment and the number of weeks between experiments to match your protocol:

- Default (start `4W`, every `4W`): `4W` → `1`, `8W` → `2`, `44W` → `11`
- Start `2W`, every `3W`: `2W` → `1`, `5W` → `2`, `8W` → `3`

Weeks that are not on the schedule show a warning in the terminal.

```
2199_1R_44W_01_BEAM_WT_F_out_processed_filtered.xlsx
```
becomes:

| Ids | Experimental Group | Gender | Test | Timepoint | …statistics |
|---|---|---|---|---|---|
| 2199_1R | WT | F | BEAM | 11 | … |

### 4. Merge Data

This tool combines several workbooks into one. For each sheet name, it stacks the rows from every file, then sorts them by the `Ids` column. Use it to join results from different batches or experiments.

### Other features

- Live, copyable log for each task
- A global **Stop** button that ends all running tasks at once
- Light and dark theme

---

## Getting started

### Requirements

- Python 3.10 or newer
- [uv](https://docs.astral.sh/uv/) (recommended), or `pip`

### Run the app

Run all commands from the project root folder. The app finds its processing scripts at `src/`.

```bash
uv run flet run
```

To run it in a browser instead:

```bash
uv run flet run --web
```

<details>
<summary>Without uv</summary>

```bash
pip install "flet[all]" pandas numpy openpyxl python-calamine xlsxwriter
flet run
```
</details>

### Typical workflow

1. **Data Filtering**: select the raw data folder, choose the experiment settings, then click **Run**.
2. **Statistics** or **Statistics – AIO**: select the folder with the `_filtered.xlsx` files, then click **Run**.
3. *(Optional)* **Merge Data**: combine summary workbooks from different experiments.

---

## Project structure

```
src/
├── main.py               # App window, sidebar navigation, global stop button
├── ex_filtering.py       # Step 1: trim, calibrate and calculate statistics for raw files
├── desc_analysis.py      # Step 2: compile statistics into one workbook
├── desc_analysis_aio.py  # Step 3: same, with filename tag parsing
├── merge_excel.py        # Step 4: merge workbooks sheet by sheet
├── process_manager.py    # Tracks and stops background processes
├── ui/
│   ├── theme.py          # Colors and shared styles
│   ├── terminal.py       # Live log panel
│   └── views/            # One screen per tool, plus the tutorial
├── assets/               # App icons
└── legacy_v1/            # Previous version (not used by the app)
```

Each processing script runs in the background, so the interface stays responsive. It runs as a separate process, or as a thread in apps built with `flet build`. You can also run each script from the command line.

---

## Build a standalone app

```bash
flet build windows -v   # or: macos, linux, apk, ipa
```

See the [Flet publishing guide](https://docs.flet.dev/publish/) for signing and platform details.

---

## License

Licensed under the [Apache License 2.0](LICENSE).

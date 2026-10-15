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
| **3. Statistics – AIO** | Folder of `*_filtered.xlsx` files plus your filename tags | Same summary, with extra columns (group, gender, test, timepoint) parsed from file names |
| **4. Merge Data** | Two or more Excel files with the same sheets | A single workbook where each sheet is stacked from all files |

A built-in **Tutorial** page explains every option in detail.

### 1. Data Filtering

For each raw file (sheets `Positions (used)` and `Kinematics`), the app:

- **Trims the trial.** It finds the frame where the animal starts moving, based on the cutoff point you choose: tail tip, tail center, tail base or both hind paws. It finds where movement stops from the nose position.
- **Calibrates the values.** It applies the correct offset and inversion for the species (*Mus musculus* or *Acomys*), the test (groundwalk, beamwalk, gridwalk or swimming) and the camera setup (old or new).
- **Applies the hind paw cutoff (optional).** It blanks out values after the hind paw reaches the height threshold.
- **Calculates statistics.** It appends Mean, Std, Median, Min, Max, Max-Normalized Mean, CV and Time Duration.

Files are processed in parallel on all CPU cores. If an output file already exists, the app skips it, so you can safely re-run an interrupted batch.

### 2. Statistics

This tool collects the statistics from every filtered file into one Excel workbook. It creates one sheet per statistic (`Mean`, `Std`, `Median`, `Min`, `Max`, `Max_Normalized_Mean`, `CV`, `Time Duration`). You can average the repeated trials of each subject (`_1`, `_2`, …) or keep each trial as its own row.

### 3. Statistics – AIO (All-In-One)

This tool does the same as Statistics. It also reads **tags** from the file names and turns them into columns. You define what each tag means. For example:

- `WT`, `TG` → *Experimental Group*
- `F`, `M` → *Gender*
- `BEAM` → *Test*

Week codes such as `44W` automatically become a **Timepoint** column (weeks ÷ 4, so `44W` → `11`).

```
2199_1R_44W_01_BEAM_WT_F_out_processed_filtered.xlsx
```
becomes:

| Ids | Experimental Group | Gender | Test | Timepoint | …statistics |
|---|---|---|---|---|---|
| 2199_1R | WT | F | BEAM | 11 | … |

### 4. Merge Data

This tool combines several workbooks into one. For each sheet name, it stacks the rows from every file. Use it to join results from different batches or experiments.

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

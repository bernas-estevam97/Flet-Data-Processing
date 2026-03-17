import os
import pandas as pd
import numpy as np
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import sys

# --- GLOBALS (Moved outside worker to save initialization time) ---
CHOICE_MAP = {
    "0": '/Feature/Tail/Tip_X',
    "1": '/Feature/Tail/Center_X',
    "2": '/Feature/Tail/Base_X',
    "3": ['/Feature/Paw/Hind/Left_X', '/Feature/Paw/Hind/Right_X']
}

SUBTRACTION_MAP = {
    ("0", "groundwalk", "old"): 0.515,
    ("1", "groundwalk", "old"): 0.505,
    ("0", "groundwalk", "new"): 0.491,
    ("0", "beamwalk", "old"): 0.44,
    ("1", "beamwalk", "old"): 0.438,
    ("0", "beamwalk", "new"): 0.426,
    ("0", "gridwalk", "old"): 0.495,
    ("0", "gridwalk", "new"): 0.473,
    ("1", "gridwalk", "old"): 0.483,
    ("0", "swimming", "old"): 0.452
}

# --- WORKER FUNCTION ---
def filter_excel_by_column(file_info_tuple, choice, animal_choice, experiment, old_or_new):
    # Unpack the file info
    index, file_path, total_files = file_info_tuple
    
    column_targets = CHOICE_MAP.get(choice)
    if not column_targets:
         return f"[ERROR] Invalid choice '{choice}'."

    try:
        # OPTIMIZATION: Use calamine for vastly faster reads
        with pd.ExcelFile(file_path, engine='calamine') as xls:
            df_raw = pd.read_excel(xls, sheet_name='Positions (used)')
            df_kin = pd.read_excel(xls, sheet_name='Kinematics')

        # --- 1. Find Start/End Indices (Threshold-based) ---
        threshold = 0.00001
        
        # Clean up entirely blank rows to ensure 1:1 index mapping
        df_raw_clean = df_raw.dropna(how='all').reset_index(drop=True)
        df_kin_clean = df_kin.dropna(how='all').reset_index(drop=True)

        if isinstance(column_targets, list):
            first_vals = df_raw_clean[column_targets].iloc[0]
            change_mask = ((df_raw_clean[column_targets] - first_vals).abs() > threshold).any(axis=1)
            movement_indices = df_raw_clean.index[change_mask]
        else:
            first_val = df_raw_clean[column_targets].iloc[0]
            movement_indices = df_raw_clean.index[(df_raw_clean[column_targets] - first_val).abs() > threshold]
        
        # Safety check: If the animal never moved past the threshold
        if movement_indices.empty:
            return f"[WARNING] File '{os.path.basename(file_path)}': No movement detected above threshold."

        start_index = movement_indices[0]

        nose_col = '/Feature/Head/Nose_X'
        if nose_col in df_raw_clean.columns:
            final_static_val = df_raw_clean[nose_col].iloc[-1]
            end_movement_indices = df_raw_clean.index[(df_raw_clean[nose_col] - final_static_val).abs() > threshold]
            last_index = end_movement_indices[-1] if not end_movement_indices.empty else len(df_raw_clean) - 1
        else:
            last_index = len(df_raw_clean) - 1

        # --- 2. Filter Kinematics ---
        # NOTE: We use df_kin_clean here so the indices match perfectly with df_raw_clean
        df_kin_filtered = df_kin_clean.iloc[start_index : last_index + 1].copy()

        # 3. Apply Subtraction & Inversion (ONLY if combination exists)
        target_indices = [5, 6, 9, 11, 13, 17]
        current_combo = (animal_choice, experiment, old_or_new)
        
        value_to_subtract = SUBTRACTION_MAP.get(current_combo)

        if value_to_subtract is not None:
            # Applying fixed_value - x logic
            df_kin_filtered.iloc[:, target_indices] = value_to_subtract - df_kin_filtered.iloc[:, target_indices]
        else:
            print(f"  [INFO] No subtraction rule for {current_combo}. Skipping inversion.")

        # --- OPTIMIZATION: Replace zeros using np.where instead of .replace() ---
        cols_to_replace_zero = df_kin_filtered.columns[26:50]
        for col in cols_to_replace_zero:
            df_kin_filtered[col] = np.where(df_kin_filtered[col] == 0, np.nan, df_kin_filtered[col])

        # 4. Hind Paw Timestamp Logic
        hind_paw_col = '/Feature/Paw/Tao/Hind/Left_X'
        if hind_paw_col in df_raw.columns and 'Time' in df_raw.columns:
            hind_reach = df_raw[df_raw[hind_paw_col] >= -0.016]
            if not hind_reach.empty:
                hind_timestamp = df_raw.loc[hind_reach.index[0], "Time"]
                cols_F_to_S = df_kin_filtered.columns[5:19]
                mask_time = df_kin_filtered['Time'] > hind_timestamp
                df_kin_filtered.loc[mask_time, cols_F_to_S] = np.nan # Replaced pd.NA with np.nan

        # 5. Statistics and Saving
        time_series = df_kin_filtered['Time'].dropna()
        time_duration = (time_series.iloc[-1] - time_series.iloc[0]) if not time_series.empty else 0
        numeric_cols = df_kin_filtered.columns[1:] 
        
        stats_block = df_kin_filtered[numeric_cols].agg(['mean', 'std', 'median', 'min', 'max'])
        stats_block.index = stats_block.index.str.title()
        stats_output = stats_block.reset_index()
        stats_output.columns = [df_kin_filtered.columns[0]] + list(numeric_cols)

        # --- FIX: Avoid Pandas FutureWarning by building a list first ---
        row_data = [np.nan] * len(df_kin_filtered.columns)
        row_data[0] = 'Time Duration'
        row_data[1] = time_duration
        duration_df = pd.DataFrame([row_data], columns=df_kin_filtered.columns)

        output_file = os.path.splitext(file_path)[0] + '_filtered.xlsx'
        
        # OPTIMIZATION: Use xlsxwriter for much faster creation of new files
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            df_raw.to_excel(writer, sheet_name='Positions (used)', index=False)
            df_kin_filtered.to_excel(writer, sheet_name='Kinematics', index=False)
            start_row = len(df_kin_filtered) + 2
            duration_df.to_excel(writer, sheet_name='Kinematics', startrow=start_row, index=False, header=False)
            stats_output.to_excel(writer, sheet_name='Kinematics', startrow=start_row + 1, index=False, header=False)

        return f"Processed file {index + 1} of {total_files}: {os.path.basename(file_path)}"

    except Exception as e:
        return f"[ERROR] File '{os.path.basename(file_path)}': {e}"


# --- MAIN EXECUTION ---
def main():
    # 1. Catch variables from Flet via sys.argv
    if len(sys.argv) > 1:
        folder_input = sys.argv[1]
        
        # Unpack the new arguments sent from the Flet dropdowns
        choice = sys.argv[2] if len(sys.argv) > 2 else "0"
        animal_choice = sys.argv[3] if len(sys.argv) > 3 else "0"
        experiment = sys.argv[4] if len(sys.argv) > 4 else "groundwalk"
        old_or_new = sys.argv[5] if len(sys.argv) > 5 else "old"
        
        print(f"🚀 Running via Flet UI in automated mode...")
        print(f"📁 Target Folder: {folder_input}")
        print(f"⚙️  Settings: Cutoff({choice}) | Animal({animal_choice}) | {experiment} | {old_or_new} camera")
        
        if not os.path.isdir(folder_input):
            print(f"[ERROR] The provided path is not a valid directory: {folder_input}")
            sys.exit(1)

    # 2. Fallback to terminal inputs if you run it manually without Flet
    else:
        while True:
            folder_input = input('\nWhich folder has your .xlsx files? ').strip()
            if os.path.isdir(folder_input):
                break
            print("❌ Invalid folder path. Please try again.")

        def get_valid_input(prompt, valid_options, error_msg):
            while True:
                val = input(prompt).strip().lower()
                if val in valid_options:
                    return val
                print(f"❌ {error_msg}")

        print("\n0 - Tail Tip | 1 - Tail Center | 2 - Tail Base | 3 - Both Paws")
        choice = get_valid_input("Cutoff starts where (0-3)? ", ["0", "1", "2", "3"], "Choose 0, 1, 2, or 3.")

        print("\n0 - Mus Musculus | 1 - Acomys")
        animal_choice = get_valid_input("Animal species: ", ["0", "1"], "Choose 0 or 1.")

        print("\nExperiments: Groundwalk, Gridwalk, Beamwalk, Swimming")
        experiment = get_valid_input("Experiment type: ", ["groundwalk", "gridwalk", "beamwalk", "swimming"], "Invalid experiment name.")

        print("\nCamera Settings: Old | New")
        old_or_new = get_valid_input("Old or New settings? ", ["old", "new"], "Choose 'old' or 'new'.")

    # --- 3. PRE-FLIGHT COMBO CHECK ---
    valid_combos = [
        ("0", "groundwalk", "old"), ("0", "groundwalk", "new"),
        ("0", "beamwalk", "old"),   ("0", "beamwalk", "new"),
        ("0", "gridwalk", "old"),   ("0", "gridwalk", "new"),
        ("1", "gridwalk", "old"),   ("0", "swimming", "old"),
        ("1", "beamwalk", "old")
    ]
    
    current_combo = (animal_choice, experiment, old_or_new)
    if current_combo not in valid_combos:
        print(f"\n⚠️  WARNING: The combination {current_combo} does not have a subtraction value.")
        if len(sys.argv) == 1:
            confirm = input("Continue anyway without coordinate inversion? (y/n): ").lower()
            if confirm != 'y':
                return

    # --- 4. PREPARE FILE LIST ---
    file_paths = [
        os.path.join(folder_input, f) 
        for f in os.listdir(folder_input) 
        if f.lower().endswith('.xlsx') and not f.startswith('~$')
    ]
    
    if not file_paths:
        print("⚠️ No Excel files found in that directory.")
        return

    total_files = len(file_paths)
    indexed_files = [(i, f, total_files) for i, f in enumerate(file_paths)]
    num_processes = os.cpu_count() or 4
    
    print(f"\n⚙️  Processing {total_files} files using {num_processes} cores...")
    
    start_time = time.perf_counter()
    
    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        futures = [
            executor.submit(filter_excel_by_column, item, choice, animal_choice, experiment, old_or_new) 
            for item in indexed_files
        ]
        
        for future in as_completed(futures):
            result = future.result()
            print(result)

    end_time = time.perf_counter()
    print(f"\n✅ Done in {round(end_time - start_time, 2)} seconds.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Exited cleanly by user request.")
        sys.exit(0)
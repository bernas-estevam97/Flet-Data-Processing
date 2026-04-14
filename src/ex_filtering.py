import os
import pandas as pd
import numpy as np
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import sys
import warnings

# Suppress pandas concatenation warnings for all-NA columns
warnings.filterwarnings("ignore", category=FutureWarning, module="pandas.core.reshape.concat")

# --- GLOBALS ---
CHOICE_MAP = {
    "0": '/Feature/Tail/Tip_X',
    "1": '/Feature/Tail/Center_X',
    "2": '/Feature/Tail/Base_X',
    "3": ['/Feature/Paw/Hind/Left_X', '/Feature/Paw/Hind/Right_X']
}

SUBTRACTION_MAP = {
    ("0", "groundwalk", "old"): 0.524,
    ("1", "groundwalk", "old"): 0.524,
    ("0", "groundwalk", "new"): 0.502,
    ("0", "beamwalk", "old"): 0.44,
    ("1", "beamwalk", "old"): 0.444,
    ("0", "beamwalk", "new"): 0.43,
    ("0", "gridwalk", "old"): 0.507,
    ("0", "gridwalk", "new"): 0.486,
    ("1", "gridwalk", "old"): 0.504,
    ("0", "swimming", "old"): 0.566, #value takes offset into account
    ("0", "swimming", "new"): 0.568, #value takes offset into account
}

OFFSET_MAP = {
    ("0", "groundwalk", "old"): 0,
    ("1", "groundwalk", "old"): 0,
    ("0", "groundwalk", "new"): 0,
    ("0", "beamwalk", "old"): 0,
    ("1", "beamwalk", "old"): 0,
    ("0", "beamwalk", "new"): 0,
    ("0", "gridwalk", "old"): 0,
    ("0", "gridwalk", "new"): 0,
    ("1", "gridwalk", "old"): 0,
    ("0", "swimming", "old"): 0.029,
    ("0", "swimming", "new"): 0.036,
}

# --- WORKER FUNCTION ---
def filter_excel_by_column(file_info_tuple, choice, animal_choice, experiment, old_or_new, output_folder):
    index, file_path, total_files = file_info_tuple
    
    column_targets = CHOICE_MAP.get(choice)
    if not column_targets:
         return f"[ERROR] Invalid choice '{choice}'."

    try:
        with pd.ExcelFile(file_path, engine='calamine') as xls:
            df_raw = pd.read_excel(xls, sheet_name='Positions (used)')
            df_kin = pd.read_excel(xls, sheet_name='Kinematics')

        # --- 1. Find Start/End Indices ---
        threshold = 0.00001
        df_raw_clean = df_raw.dropna(how='all').reset_index(drop=True)
        df_kin_clean = df_kin.dropna(how='all').reset_index(drop=True)

        if isinstance(column_targets, list):
            first_vals = df_raw_clean[column_targets].iloc[0]
            change_mask = ((df_raw_clean[column_targets] - first_vals).abs() > threshold).any(axis=1)
            movement_indices = df_raw_clean.index[change_mask]
        else:
            first_val = df_raw_clean[column_targets].iloc[0]
            movement_indices = df_raw_clean.index[(df_raw_clean[column_targets] - first_val).abs() > threshold]
        
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
        df_kin_filtered = df_kin_clean.iloc[start_index : last_index + 1].copy()

        # --- 3. Apply Subtraction & Inversion ---
        target_indices = [5, 6, 9, 11, 13, 17]

        # --- NEW DYNAMIC INDEX LOGIC ---
        # Check Nose Height (index 15) and Tail Tip Height (index 16)
        if df_kin_filtered.iloc[:, 15].mean() > 0.3:
            target_indices.append(15)
        if df_kin_filtered.iloc[:, 16].mean() > 0.3:
            target_indices.append(16)
        # -------------------------------

        target_indices_offset = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]

        current_combo = (animal_choice, experiment, old_or_new)
        value_to_subtract = SUBTRACTION_MAP.get(current_combo)
        value_to_subtract_offset = OFFSET_MAP.get(current_combo)

        if value_to_subtract_offset is not None:
                df_kin_filtered.iloc[:, target_indices_offset] -= value_to_subtract_offset

        if value_to_subtract is not None:
            df_kin_filtered.iloc[:, target_indices] = value_to_subtract - df_kin_filtered.iloc[:, target_indices]

        cols_to_replace_zero = df_kin_filtered.columns[26:50]
        for col in cols_to_replace_zero:
            df_kin_filtered[col] = np.where(df_kin_filtered[col] == 0, np.nan, df_kin_filtered[col])

        # --- 4. Hind Paw Timestamp Logic ---
        hind_paw_col = '/Feature/Paw/Tao/Hind/Left_X'
        if hind_paw_col in df_raw.columns and 'Time' in df_raw.columns:
            hind_reach = df_raw[df_raw[hind_paw_col] >= -0.016]
            if not hind_reach.empty:
                hind_timestamp = df_raw.loc[hind_reach.index[0], "Time"]
                cols_F_to_S = df_kin_filtered.columns[5:19]
                mask_time = df_kin_filtered['Time'] > hind_timestamp
                df_kin_filtered.loc[mask_time, cols_F_to_S] = np.nan 

        # --- 5. Statistics and Saving (OPTIMIZED) ---
        time_series = df_kin_filtered['Time'].dropna()
        time_duration = (time_series.iloc[-1] - time_series.iloc[0]) if not time_series.empty else 0
        numeric_cols = df_kin_filtered.columns[1:] 
        
        stats_block = df_kin_filtered[numeric_cols].agg(['mean', 'std', 'median', 'min', 'max'])
        stats_block.index = stats_block.index.str.title()
        stats_output = stats_block.reset_index()
        stats_output.columns = [df_kin_filtered.columns[0]] + list(numeric_cols)

        row_data = [np.nan] * len(df_kin_filtered.columns)
        row_data[0] = 'Time Duration'
        row_data[1] = time_duration
        duration_df = pd.DataFrame([row_data], columns=df_kin_filtered.columns)

        # 🚀 NEW: Combine everything in memory before writing
        spacer = pd.DataFrame([[np.nan] * len(df_kin_filtered.columns)], columns=df_kin_filtered.columns)
        
        final_kinematic_sheet = pd.concat([
            df_kin_filtered, 
            spacer, 
            duration_df, 
            stats_output
        ], ignore_index=True)

        # 🚀 NEW: Save to the designated output folder instead of the input folder
        base_name = os.path.basename(file_path)
        name_only = os.path.splitext(base_name)[0]
        output_file = os.path.join(output_folder, f"{name_only}_filtered.xlsx")
        
        # 🚀 NEW: Write the sheet exactly once
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            df_raw.to_excel(writer, sheet_name='Positions (used)', index=False)
            final_kinematic_sheet.to_excel(writer, sheet_name='Kinematics', index=False)

        return f"Processed file {index + 1} of {total_files}: {os.path.basename(file_path)}"

    except Exception as e:
        print(f"[ERROR] File '{os.path.basename(file_path)}': {e}") # This sends it to the UI!
        return f"[ERROR] File '{os.path.basename(file_path)}': {e}" # This keeps your internal logic working

# --- MAIN EXECUTION ---
def main():
    if len(sys.argv) > 1:
        folder_input = sys.argv[1]
        choice = sys.argv[2] if len(sys.argv) > 2 else "0"
        animal_choice = sys.argv[3] if len(sys.argv) > 3 else "0"
        experiment = sys.argv[4] if len(sys.argv) > 4 else "groundwalk"
        old_or_new = sys.argv[5] if len(sys.argv) > 5 else "old"
        
        # 🚀 NEW: Check for a 6th argument. If it's missing or blank, default to folder_input
        output_folder = sys.argv[6] if len(sys.argv) > 6 and sys.argv[6].strip() else folder_input
        
        # Create it if it somehow doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        print(f"🚀 Running via Flet UI in automated mode...")
        print(f"📁 Input Folder: {folder_input}")
        print(f"📁 Output Folder: {output_folder}")
        print(f"⚙️  Settings: Cutoff({choice}) | Animal({animal_choice}) | {experiment} | {old_or_new} camera")
        
        if not os.path.isdir(folder_input):
            print(f"[ERROR] The provided path is not a valid directory: {folder_input}")
            sys.exit(1)

    else:
        while True:
            folder_input = input('\nWhich folder has your .xlsx files? ').strip()
            if os.path.isdir(folder_input):
                break
            print("❌ Invalid folder path. Please try again.")
            
        # 🚀 NEW: Ask for output folder, default to input if blank
        output_folder_input = input('Which folder for output? (Press Enter to use the input folder): ').strip()
        output_folder = output_folder_input if output_folder_input else folder_input
        os.makedirs(output_folder, exist_ok=True)

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

    # 🚀 NEW: Leave 2 cores free to prevent UI lockups
    num_processes = max(1, (os.cpu_count() or 4) - 2)
    
    print(f"\n⚙️  Processing {total_files} files using {num_processes} cores...")
    
    start_time = time.perf_counter()
    
    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        futures = [
            executor.submit(filter_excel_by_column, item, choice, animal_choice, experiment, old_or_new, output_folder) 
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
import os
import pandas as pd
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import sys

# --- WORKER FUNCTION ---
# Now accepts two separate arguments:
# 1. file_info_tuple: The variable data (index, file path, counts)
# 2. choice: The constant setting (0, 1, or 2)
def filter_excel_by_column(file_info_tuple, choice, animal_choice, experiment, old_or_new):
    # Unpack the file info
    index, file_path, total_files = file_info_tuple
    
    choice_map = {
        "0": '/Feature/Tail/Tip_X',
        "1": '/Feature/Tail/Center_X',
        "2": '/Feature/Tail/Base_X',
        "3": ['/Feature/Paw/Hind/Left_X', '/Feature/Paw/Hind/Right_X']
    }
    
    # --- SUBTRACTION CONFIGURATION MAP ---
    # format: (animal, experiment, age) : value
    subtraction_map = {
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

    column_targets = choice_map.get(choice)
    if not column_targets:
         return f"[ERROR] Invalid choice '{choice}'."

    try:
        with pd.ExcelFile(file_path) as xls:
            df_raw = pd.read_excel(xls, sheet_name='Positions (used)')
            df_kin = pd.read_excel(xls, sheet_name='Kinematics')

        # 1. Find Start/End Indices
        if isinstance(column_targets, list):
            mask = df_raw[column_targets].notna().all(axis=1)
        else:
            mask = df_raw[column_targets].notna()

        valid_indices = df_raw.index[mask]
        if valid_indices.empty:
            return f"[WARNING] File '{os.path.basename(file_path)}': No valid data overlap."
        
        start_index = valid_indices[0]
        last_index = df_raw['/Feature/Head/Nose_X'].last_valid_index()

        # 2. Filter Kinematics
        df_kin_filtered = df_kin.iloc[start_index : last_index + 1].copy()

        # 3. Apply Subtraction & Inversion (ONLY if combination exists)

        # IF VIDEO PROCESSING WAS DONE WITH WRONG OFFSET MAYBE NEED TO SUBTRACT MORE 
        #-6.8 ---> BEAM
        #  

        target_indices = [5, 6, 9, 11, 13, 15, 16, 17]
        current_combo = (animal_choice, experiment, old_or_new)
        
        value_to_subtract = subtraction_map.get(current_combo)

        if value_to_subtract is not None:
            # Applying fixed_value - x logic
            df_kin_filtered.iloc[:, target_indices] = value_to_subtract - df_kin_filtered.iloc[:, target_indices]
        else:
            # This is your "if no combination is found" safety net
            # It logs to the console so you know which files didn't get modified
            print(f"  [INFO] No subtraction rule for {current_combo}. Skipping inversion.")

        # --- NEW: Replace zeros in columns AA (26) through AX (49) ---
        # We use index 50 as the stop because slicing [start:stop] is exclusive.
        
        # Select the target range
        cols_to_replace_zero = df_kin_filtered.columns[26:50]
        
        # Replace zeros with NaN so they are ignored by median/mean/std
        df_kin_filtered[cols_to_replace_zero] = df_kin_filtered[cols_to_replace_zero].replace(0, pd.NA)


        # 4. Hind Paw Timestamp Logic
        hind_paw_col = '/Feature/Paw/Tao/Hind/Left_X'
        if hind_paw_col in df_raw.columns and 'Time' in df_raw.columns:
            hind_reach = df_raw[df_raw[hind_paw_col] >= -0.016]
            if not hind_reach.empty:
                hind_timestamp = df_raw.loc[hind_reach.index[0], "Time"]
                cols_F_to_S = df_kin_filtered.columns[5:19]
                mask_time = df_kin_filtered['Time'] > hind_timestamp
                df_kin_filtered.loc[mask_time, cols_F_to_S] = pd.NA

        # 5. Statistics and Saving... (rest of your logic remains the same)
        time_series = df_kin_filtered['Time'].dropna()
        time_duration = (time_series.iloc[-1] - time_series.iloc[0]) if not time_series.empty else 0
        numeric_cols = df_kin_filtered.columns[1:] 
        stats_block = df_kin_filtered[numeric_cols].agg(['mean', 'std', 'median', 'min', 'max'])
        stats_block.index = stats_block.index.str.title()
        stats_output = stats_block.reset_index()
        stats_output.columns = [df_kin_filtered.columns[0]] + list(numeric_cols)

        duration_df = pd.DataFrame([[pd.NA] * len(df_kin_filtered.columns)], columns=df_kin_filtered.columns)
        duration_df.iloc[0, 0] = 'Time Duration'
        duration_df.iloc[0, 1] = time_duration

        output_file = os.path.splitext(file_path)[0] + '_filtered.xlsx'
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
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
    # sys.argv[0] is the script name itself, sys.argv[1] is the first argument (data_path)
    # 1. Catch variables from Flet via sys.argv
    if len(sys.argv) > 1:
        folder_input = sys.argv[1]
        
        # Unpack the new arguments sent from the Flet dropdowns
        # We use a fallback just in case the arguments weren't sent properly
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
        # If running via UI, we bypass the confirm input and proceed automatically
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
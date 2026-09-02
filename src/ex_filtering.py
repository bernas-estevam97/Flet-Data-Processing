import os
import sys
import time
import traceback
import datetime
import warnings
import pandas as pd
import numpy as np
import concurrent.futures
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

# Reconfigure stdout to utf-8 on Windows if needed
if sys.stdout.encoding is not None and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

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
    ("0", "groundwalk", "old"): 0.522,
    ("1", "groundwalk", "old"): 0.525,
    ("0", "groundwalk", "new"): 0.502,
    ("1", "groundwalk", "new"): 0.519,
    ("0", "beamwalk", "old"): 0.445,
    ("1", "beamwalk", "old"): 0.445,
    ("0", "beamwalk", "new"): 0.43,
    ("1", "beamwalk", "new"): 0.44,
    ("0", "gridwalk", "old"): 0.496,
    ("0", "gridwalk", "new"): 0.483,
    ("1", "gridwalk", "old"): 0.504,
    ("1", "gridwalk", "new"): 0.498,
    ("0", "swimming", "old"): 0.566,
    ("0", "swimming", "new"): 0.568,
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
def filter_excel_by_column(file_info_tuple, choice, animal_choice, experiment, old_or_new, output_folder, height_cutoff="no"):
    index, file_path, total_files = file_info_tuple
    file_name = os.path.basename(file_path)
    captured_warnings = []

    column_targets = CHOICE_MAP.get(choice)
    if not column_targets:
        return (False, file_name, f"[ERROR] Invalid choice '{choice}'.", [], False)

    # --- 1. Determine Output Path and Check if it Exists ---
    output_file = os.path.join(output_folder, os.path.splitext(file_name)[0] + '_filtered.xlsx')

    if os.path.exists(output_file):
        return (True, file_name, f"Skipped file {index + 1} of {total_files}: {file_name} (Already exists)", [], True)

    try:
        with warnings.catch_warnings(record=True) as w_log:
            warnings.simplefilter("always") 
            
            # Attempt reading with calamine engine, fallback to openpyxl if engine error occurs
            try:
                with pd.ExcelFile(file_path, engine='calamine') as xls:
                    df_raw = pd.read_excel(xls, sheet_name='Positions (used)')
                    df_kin = pd.read_excel(xls, sheet_name='Kinematics')
            except Exception:
                df_raw = pd.read_excel(file_path, sheet_name='Positions (used)')
                df_kin = pd.read_excel(file_path, sheet_name='Kinematics')

            # --- 2. Find Start/End Indices ---
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
            
            start_index = movement_indices[0] if not movement_indices.empty else 0

            nose_col = '/Feature/Head/Nose_X'
            if nose_col in df_raw_clean.columns:
                final_static_val = df_raw_clean[nose_col].iloc[-1]
                end_movement_indices = df_raw_clean.index[(df_raw_clean[nose_col] - final_static_val).abs() > threshold]
                last_index = end_movement_indices[-1] if not end_movement_indices.empty else len(df_raw_clean) - 1
            else:
                last_index = len(df_raw_clean) - 1

            # 3. Filter Kinematics & Cast Numeric Columns to Float
            df_kin_filtered = df_kin_clean.iloc[start_index : last_index + 1].copy()

            numeric_cols = [col for col in df_kin_filtered.columns if col != 'Time']
            for col in numeric_cols:
                df_kin_filtered[col] = pd.to_numeric(df_kin_filtered[col], errors='coerce').astype(float)

            # 4. Apply Subtraction & Inversion
            target_indices = [5, 6, 9, 11, 13, 21, 23] if experiment == "gridwalk" else [5, 6, 9, 11, 13, 17]

            def safe_mean_gt(df, col_idx, thresh=0.3):
                if col_idx < df.shape[1]:
                    s = df.iloc[:, col_idx].dropna()
                    return not s.empty and s.mean() > thresh
                return False

            if experiment == "gridwalk":
                if safe_mean_gt(df_kin_filtered, 15): target_indices.append(15)
                if safe_mean_gt(df_kin_filtered, 19): target_indices.append(19)
                if safe_mean_gt(df_kin_filtered, 20): target_indices.append(20)
            else:
                if safe_mean_gt(df_kin_filtered, 15): target_indices.append(15)
                if safe_mean_gt(df_kin_filtered, 16): target_indices.append(16)
            
            target_indices_offset = [i for i in [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18] if i < df_kin_filtered.shape[1]]
            target_indices = [i for i in target_indices if i < df_kin_filtered.shape[1]]
            current_combo = (animal_choice, experiment, old_or_new)
            
            value_to_subtract = SUBTRACTION_MAP.get(current_combo)
            value_to_add_offset = OFFSET_MAP.get(current_combo)

            if value_to_add_offset is not None and target_indices_offset:
                df_kin_filtered.iloc[:, target_indices_offset] += value_to_add_offset

            if value_to_subtract is not None and target_indices:
                df_kin_filtered.iloc[:, target_indices] = value_to_subtract - df_kin_filtered.iloc[:, target_indices]

            # Replace 0 with np.nan safely on available numeric columns 26:50
            max_col = min(50, df_kin_filtered.shape[1])
            if max_col > 26:
                cols_to_replace_zero = df_kin_filtered.columns[26:max_col]
                df_kin_filtered[cols_to_replace_zero] = df_kin_filtered[cols_to_replace_zero].replace(0, np.nan)

            # 5. Hind Paw Timestamp Logic
            if str(height_cutoff).lower() in ["yes", "true", "1"]:
                hind_paw_col = '/Feature/Paw/Tao/Hind/Left_X' 
                
                if hind_paw_col in df_raw_clean.columns and 'Time' in df_raw_clean.columns:
                    threshold_val = 0 if old_or_new == "new" else -0.016
                    hind_reach = df_raw_clean[df_raw_clean[hind_paw_col] >= threshold_val]
                    
                    if not hind_reach.empty:
                        hind_timestamp = df_raw_clean.loc[hind_reach.index[0], "Time"]
                        cols_F_to_S = df_kin_filtered.columns[5:min(19, df_kin_filtered.shape[1])]
                        mask_time = df_kin_filtered['Time'] > hind_timestamp
                        df_kin_filtered.loc[mask_time, cols_F_to_S] = np.nan

            # 6. Statistics and Saving
            time_series = df_kin_filtered['Time'].dropna() if 'Time' in df_kin_filtered.columns else pd.Series(dtype=float)
            time_duration = (time_series.iloc[-1] - time_series.iloc[0]) if not time_series.empty else 0
            stats_cols = [col for col in df_kin_filtered.columns if col != 'Time']
            
            def max_norm_mean(col):
                clean_col = col.dropna()
                if clean_col.empty:
                    return np.nan
                max_val = clean_col.max()
                if pd.isna(max_val) or max_val == 0:
                    return np.nan
                return (clean_col / max_val).mean()

            def coef_var(col):
                clean_col = col.dropna()
                if clean_col.empty:
                    return np.nan
                mean_val = clean_col.mean()
                if pd.isna(mean_val) or mean_val == 0:
                    return np.nan
                return clean_col.std() / mean_val
            
            stats_block = df_kin_filtered[stats_cols].agg(['mean', 'std', 'median', 'min', 'max', max_norm_mean, coef_var])
            
            formatted_index = []
            for idx in stats_block.index:
                if idx == 'max_norm_mean':
                    formatted_index.append('Max_Normalized_Mean')
                elif idx == 'coef_var':
                    formatted_index.append('CV')
                else:
                    formatted_index.append(str(idx).title())
            stats_block.index = formatted_index
            
            stats_output = stats_block.reset_index()
            stats_output.columns = [df_kin_filtered.columns[0]] + list(stats_cols)

            row_data = [np.nan] * len(df_kin_filtered.columns)
            row_data[0] = 'Time Duration'
            if len(row_data) > 1:
                row_data[1] = time_duration
            duration_df = pd.DataFrame([row_data], columns=df_kin_filtered.columns)

            with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
                df_raw.to_excel(writer, sheet_name='Positions (used)', index=False)
                df_kin_filtered.to_excel(writer, sheet_name='Kinematics', index=False)
                start_row = len(df_kin_filtered) + 2
                duration_df.to_excel(writer, sheet_name='Kinematics', startrow=start_row, index=False, header=False)
                stats_output.to_excel(writer, sheet_name='Kinematics', startrow=start_row + 1, index=False, header=False)

            for w in w_log:
                captured_warnings.append(f"{w.category.__name__}: {str(w.message)}")

        return (True, file_name, f"Processed file {index + 1} of {total_files}: {file_name}", captured_warnings, False)

    except Exception as e:
        error_msg = f"{e}\n{traceback.format_exc()}"
        return (False, file_name, error_msg, [], False)


# --- MAIN EXECUTION ---
def main():
    if len(sys.argv) > 1:
        folder_input = sys.argv[1]
        choice = sys.argv[2] if len(sys.argv) > 2 else "0"
        animal_choice = sys.argv[3] if len(sys.argv) > 3 else "0"
        experiment = sys.argv[4] if len(sys.argv) > 4 else "groundwalk"
        old_or_new = sys.argv[5] if len(sys.argv) > 5 else "old"
        output_folder = sys.argv[6] if len(sys.argv) > 6 and sys.argv[6].strip() else folder_input
        height_cutoff = sys.argv[7] if len(sys.argv) > 7 else "no"

        os.makedirs(output_folder, exist_ok=True)

        print(f"[START] Running excel filtering...")
        print(f"[PATH] Input Folder: {folder_input}")
        print(f"[PATH] Output Folder: {output_folder}")
        print(f"[CONFIG] Settings: Cutoff({choice}) | Animal({animal_choice}) | {experiment} | {old_or_new} | Height Cutoff: {height_cutoff}")

        if not os.path.isdir(folder_input):
            print(f"[ERROR] The provided input path is not a valid directory: {folder_input}")
            sys.exit(1)

    else:
        # Interactive Mode
        while True:
            folder_input = input('\nWhich folder has your .xlsx files? ').strip()
            folder_output = input('\nWhich folder you wish to place your filtered files (if empty it will be the same as the input folder)? ').strip()
            
            if not folder_output:
                folder_output = folder_input
                
            if os.path.isdir(folder_input) and os.path.isdir(folder_output):
                print(f'\nInput folder: {os.path.basename(os.path.normpath(folder_input))}          Output folder: {os.path.basename(os.path.normpath(folder_output))}')
                break
                
            print("\n[!] Invalid folder path. Check your input and output folder paths and please try again.")
            
        def get_valid_input(prompt, valid_options, error_msg):
            while True:
                val = input(prompt).strip().lower()
                if val in valid_options:
                    return val
                print(f"[!] {error_msg}")

        print("\n0 - Tail Tip | 1 - Tail Center | 2 - Tail Base | 3 - Both Paws")
        choice = get_valid_input("Cutoff starts where (0-3)? ", ["0", "1", "2", "3"], "Choose 0, 1, 2, or 3.")
        animal_choice = get_valid_input("Animal species (0: Mus, 1: Acomys): ", ["0", "1"], "Choose 0 or 1.")
        experiment = get_valid_input("Experiment type: ", ["groundwalk", "gridwalk", "beamwalk", "swimming"], "Invalid experiment.")
        old_or_new = get_valid_input("Old or New settings? ", ["old", "new"], "Choose 'old' or 'new'.")
        height_cutoff = get_valid_input("Apply hind paw height cutoff? (yes/no): ", ["yes", "no"], "Choose 'yes' or 'no'.")
        output_folder = folder_output

    file_paths = [os.path.join(folder_input, f) for f in os.listdir(folder_input) 
                  if f.lower().endswith('.xlsx') and not f.startswith('~$') and not f.endswith('_filtered.xlsx')]
    
    if not file_paths:
        print("[!] No valid Excel files found to process.")
        return
        
    total_files = len(file_paths)
    indexed_files = [(i, f, total_files) for i, f in enumerate(file_paths)]

    # Dynamic CPU Core Allocation matching optimized_excel_filtering.py
    total_cores = os.cpu_count() or 4
    num_processes = total_cores - 4 if total_cores > 8 else total_cores
    num_processes = max(1, num_processes)
    
    log_file_path = os.path.join(output_folder, "error_log.txt")
    print(f"\n[INFO] Checking {total_files} files using {num_processes} processes... Logging to: {log_file_path}")
    
    start_time = time.perf_counter()
    failed_files, files_with_warnings, skipped_files = [], [], []

    def handle_result_tuple(res_tuple, log_file):
        success, fname, message, warnings_list, is_skipped = res_tuple
        if success:
            if is_skipped:
                print(message)
                log_file.write(f"[SKIPPED] {fname}\n")
                skipped_files.append(fname)
            elif warnings_list:
                print(f"[WARN] {fname}: Processed with warnings.")
                log_file.write(f"[WARNING] {fname}\n")
                for w in warnings_list:
                    log_file.write(f"    - {w}\n")
                files_with_warnings.append(fname)
            else:
                print(message)
                log_file.write(f"[SUCCESS] {fname}\n")
        else:
            error_short = message.split('\n')[0]
            print(f"[ERROR] File '{fname}': {error_short}")
            log_file.write(f"\n[ERROR] File: {fname}\n{message}\n{'-'*30}\n")
            failed_files.append((fname, error_short))

    with open(log_file_path, 'w', encoding='utf-8') as log_file:
        log_file.write(f"--- Processing Started at {datetime.datetime.now()} ---\n")
        log_file.write(f"Parameters: Choice={choice}, Animal={animal_choice}, Exp={experiment}, Set={old_or_new}, HeightCutoff={height_cutoff}\n")
        log_file.write("-" * 50 + "\n")

        pool_broken = False
        try:
            with ProcessPoolExecutor(max_workers=num_processes) as executor:
                futures = [
                    executor.submit(filter_excel_by_column, item, choice, animal_choice, experiment, old_or_new, output_folder, height_cutoff)
                    for item in indexed_files
                ]
                
                for future in as_completed(futures):
                    try:
                        res = future.result()
                        handle_result_tuple(res, log_file)
                    except (concurrent.futures.process.BrokenProcessPool, Exception) as exc:
                        pool_broken = True
                        print(f"[WARN] Process pool interrupted ({exc}). Switching to safe execution mode...")
                        log_file.write(f"[WARNING] Process pool interrupted: {exc}\n")
                        break

        except (concurrent.futures.process.BrokenProcessPool, Exception) as pool_err:
            pool_broken = True
            print(f"[WARN] Multiprocessing pool exception ({pool_err}). Switching to safe execution mode...")
            log_file.write(f"[WARNING] Multiprocessing pool failed: {pool_err}\n")

        # Fallback processing if ProcessPool fails or breaks on external drive
        if pool_broken:
            print("\n[INFO] Running remaining files in safe sequential mode...")
            for item in indexed_files:
                file_path = item[1]
                fname = os.path.basename(file_path)
                out_file = os.path.join(output_folder, os.path.splitext(fname)[0] + '_filtered.xlsx')
                if os.path.exists(out_file) or fname in skipped_files or any(f[0] == fname for f in failed_files) or fname in [f for f in files_with_warnings]:
                    continue
                try:
                    res = filter_excel_by_column(item, choice, animal_choice, experiment, old_or_new, output_folder, height_cutoff)
                    handle_result_tuple(res, log_file)
                except Exception as exc:
                    error_str = str(exc) or exc.__class__.__name__
                    print(f"[ERROR] File '{fname}': {error_str}")
                    log_file.write(f"\n[ERROR] File: {fname}: {error_str}\n{'-'*30}\n")
                    failed_files.append((fname, error_str))

        duration = round(time.perf_counter() - start_time, 2)
        end_msg = f"\n[DONE] Finished in {duration} seconds.\n"
        
        summary_msg = f"\nTotal Files Checked: {total_files}\n"
        summary_msg += f"Processed Successfully: {total_files - len(skipped_files) - len(failed_files)}\n"
        summary_msg += f"Skipped (Already Existed): {len(skipped_files)}\n"

        if failed_files:
            summary_msg += f"\n[FAIL] {len(failed_files)} files FAILED:\n" + "".join([f"   - {f}: {err}\n" for f, err in failed_files])
        
        if files_with_warnings:
            summary_msg += f"\n[WARN] {len(files_with_warnings)} files had WARNINGS (check log):\n" + "".join([f"   - {f}\n" for f in files_with_warnings])

        if not failed_files and not files_with_warnings:
            summary_msg += "\n[OK] Processing completed without errors or warnings.\n"
        
        summary_msg += f"\nFull details saved to: '{os.path.basename(log_file_path)}'\n"

        print(end_msg + summary_msg)
        log_file.write(end_msg + summary_msg)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")

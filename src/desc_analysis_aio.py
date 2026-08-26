import os
import sys
import re
import json
import pandas as pd
from functools import partial
from multiprocessing import Pool, cpu_count

# Reconfigure stdout to utf-8 on Windows if needed
if sys.stdout.encoding is not None and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

pd.set_option('future.no_silent_downcasting', True)

def extract_data_from_excel(file_path, user_tags):
    """
    WORKER FUNCTION (Runs in parallel)
    Opens a single Excel file, extracts rows, and parses tags dynamically.
    """
    file_id = os.path.basename(file_path)
    
    try:
        df_filtered = pd.read_excel(file_path, sheet_name='Kinematics', header=None, engine='calamine')
    except Exception as e:
        return {'error': f"[ERROR] Error reading {file_id}: {e}"}

    parts = file_id.split("_")
    file_id_split = "_".join(parts[:parts.index("out")]) if "out" in parts else file_id

    # 1. Apply trial number removal for subject base_id
    cleaned_id_str = re.sub(r'_\d{1,2}(?=_|\.|$)', '', file_id_split, count=1)

    # 2. Extract Tags Dynamically based on user input
    found_meanings = []
    clean_parts = []
    
    user_tags_upper = {k.upper(): v for k, v in user_tags.items()}

    for p in cleaned_id_str.split("_"):
        p_upper = p.upper()
        if p_upper in user_tags_upper:
            found_meanings.append(user_tags_upper[p_upper])
        else:
            clean_parts.append(p)
            
    base_id = "_".join(clean_parts)
    tags_joined = " - ".join(found_meanings) if found_meanings else "Uncategorized"
    
    warning_msg = None
    if not found_meanings and user_tags:
        warning_msg = f"[WARNING] No matching tags found in filename: '{file_id}'. Assumed Base ID: '{base_id}'"

    # 3. Format Headers
    header_row_raw = df_filtered.iloc[0]
    header_stats = ["Ids", "Identified Tags"] + header_row_raw.iloc[1:].tolist()

    first_col = df_filtered.iloc[:, 0].astype(str).str.lower().str.strip()

    # 4. Extract Statistics
    stats_to_extract = {
        "mean": "Mean", 
        "std": "Std", 
        "median": "Median", 
        "min": "Min", 
        "max": "Max",
        "max_normalized_mean": "Max_Normalized_Mean",
        "cv": "CV"
    }
    extracted_stats = {}
    
    for search_term, sheet_name in stats_to_extract.items():
        mask = first_col == search_term
        found_rows = df_filtered[mask]

        if not found_rows.empty:
            stat_values = found_rows.iloc[-1]
            stat_data = stat_values.iloc[1:].tolist()
            extracted_stats[sheet_name] = stat_data

    # 5. Extract Time Duration
    duration_val = None
    mask_duration = first_col.str.contains("duration", na=False)
    found_duration_rows = df_filtered[mask_duration]
    
    if not found_duration_rows.empty:
        duration_values = found_duration_rows.iloc[-1]
        duration_val = duration_values.iloc[1]

    print(f"[EXTRACT] Read data from: {file_id}")

    return {
        'error': None,
        'warning': warning_msg,
        'file_path': file_path,
        'original_id': file_id_split,
        'base_id': base_id,
        'tags_joined': tags_joined,
        'header_stats': header_stats,
        'extracted_stats': extracted_stats,
        'duration_val': duration_val
    }

def main():
    user_tags = {}
    should_group = False
    
    # --- 1. Catch variables from Flet via sys.argv ---
    if len(sys.argv) > 1:
        folder_input = sys.argv[1]
        folder_output = sys.argv[2].strip() if len(sys.argv) > 2 and sys.argv[2].strip() else folder_input
        experiment_name = sys.argv[3].strip() if len(sys.argv) > 3 else "experiment"
        
        if len(sys.argv) > 4:
            try:
                user_tags = json.loads(sys.argv[4])
            except json.JSONDecodeError:
                print("[WARNING] Failed to parse tags JSON string from Flet UI. Defaulting to empty tags.")
                
        if len(sys.argv) > 5:
            should_group = str(sys.argv[5]).strip().lower() in ['y', 'yes', 'true', '1']

        print(f"[START] Running Data Compilation...")
        print(f"[PATH] Input Folder: {folder_input}")
        print(f"[PATH] Output Folder: {folder_output}")
        print(f"[CONFIG] Active Tags: {len(user_tags)} defined")
        print(f"[CONFIG] Trial Grouping: {'Enabled (Mean per Subject & Tags)' if should_group else 'Disabled (Keep All Trials)'}\n")
        
        if not os.path.isdir(folder_input):
            print(f"[ERROR] The provided input path is not a valid directory: {folder_input}")
            sys.exit(1)
            
        os.makedirs(folder_output, exist_ok=True)

    # --- 2. Fallback to terminal inputs if run manually ---
    else:
        folder_input = input('Which folder has your filtered xlsx files? ').strip()
        if not os.path.isdir(folder_input):
            print('[ERROR] Invalid path input.')
            return
        folder_output = input('In which folder do you want your excel file to be at (leave blank for same as input): ').strip()
        folder_output = folder_output if folder_output else folder_input
        experiment_name = input('What experiment are these files from? ').strip()
        
        group_choice = input("Do you want to group the means according to the detected IDs & Tags? (y/n): ").strip().lower()
        should_group = group_choice in ['y', 'yes']

    # --- 3. GET FILES ---
    file_paths = sorted([os.path.join(folder_input, p) for p in os.listdir(folder_input) if p.endswith('filtered.xlsx')])
    if not file_paths:
        print(f"[WARNING] No '*filtered.xlsx' files found in '{folder_input}'.")
        return
    
    total_files = len(file_paths)
    print(f"[INFO] Found {total_files} files. Starting parallel data extraction...")

    # --- PHASE 1: READ MULTIPLE FILES IN PARALLEL ---
    num_cores = max(1, cpu_count() - 2) 
    worker_func = partial(extract_data_from_excel, user_tags=user_tags)
    
    with Pool(processes=num_cores) as pool:
        results = pool.map(worker_func, file_paths)

    print("\nData extraction complete! Formatting data...")

    # --- PHASE 2: WRITE SEQUENTIALLY TO ONE EXCEL FILE ---
    compiled_stats = {sheet: [] for sheet in ["Mean", "Std", "Median", "Min", "Max", "Max_Normalized_Mean", "CV"]}
    compiled_durations = []
    master_header = None

    for res in results:
        if res['error']:
            print(res['error'])
            continue 
        if res.get('warning'):
            print(res['warning'])
            
        if master_header is None and res.get('header_stats'):
            master_header = res['header_stats']

        current_id = res['base_id'] if should_group else res['original_id']

        for sheet_name, row_data in res['extracted_stats'].items():
            if sheet_name in compiled_stats:
                compiled_stats[sheet_name].append([current_id, res['tags_joined']] + row_data)

        if res['duration_val'] is not None:
            compiled_durations.append([current_id, res['tags_joined'], res['duration_val']])

    sample_path_split = os.path.normpath(file_paths[0]).split(os.path.sep)
    dir_part_1 = sample_path_split[-3] if len(sample_path_split) >= 3 else "folder"
    dir_part_2 = sample_path_split[-2] if len(sample_path_split) >= 2 else "output"
    
    output_filename = f'{experiment_name.upper()}_descriptive_statistics_{dir_part_1}_{dir_part_2}.xlsx'
    output_path = os.path.join(folder_output, output_filename)

    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        for sheet_name, rows in compiled_stats.items():
            if rows:
                df = pd.DataFrame(rows, columns=master_header)
                numeric_cols = df.columns.drop(['Ids', 'Identified Tags'])
                df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
                
                if should_group:
                    df_grouped = df.groupby(['Ids', 'Identified Tags'], as_index=False)[numeric_cols].mean()
                else:
                    df_grouped = df
                    
                df_grouped.to_excel(writer, sheet_name=sheet_name, index=False)

        if compiled_durations:
            df_duration = pd.DataFrame(compiled_durations, columns=["Ids", "Identified Tags", "Time Duration"])
            df_duration['Time Duration'] = pd.to_numeric(df_duration['Time Duration'], errors='coerce')
            
            if should_group:
                df_duration_grouped = df_duration.groupby(['Ids', 'Identified Tags'], as_index=False).mean()
            else:
                df_duration_grouped = df_duration
                
            df_duration_grouped.to_excel(writer, sheet_name="Time Duration", index=False)

    print(f"[SUCCESS] Data saved to: {output_path}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nProgram terminated by user. Exiting...')
        sys.exit(0)

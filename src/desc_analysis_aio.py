import os
import sys
import re
import json
import pandas as pd
from multiprocessing import Pool, cpu_count

# Reconfigure stdout to utf-8 on Windows if needed
if sys.stdout.encoding is not None and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def extract_data_from_excel(file_path, user_tags):
    """
    WORKER FUNCTION (Runs in parallel)
    Opens a single Excel file, extracts rows, and parses tags dynamically.
    """
    file_id = os.path.basename(file_path)
    
    # Ignore temporary Excel lock files (e.g. ~$filename.xlsx)
    if file_id.startswith('~$') or not os.path.isfile(file_path):
        return {'error': None, 'skipped': True}

    if os.path.getsize(file_path) == 0:
        return {'error': f"[ERROR] File '{file_id}' is empty (0 bytes)."}

    df_filtered = None
    read_errors = []
    
    for engine_name in ['calamine', 'openpyxl', None]:
        try:
            if engine_name:
                df_filtered = pd.read_excel(file_path, sheet_name='Kinematics', header=None, engine=engine_name)
            else:
                df_filtered = pd.read_excel(file_path, sheet_name='Kinematics', header=None)
            break
        except Exception as err:
            read_errors.append(f"{engine_name or 'default'}: {err}")

    if df_filtered is None:
        return {'error': f"[ERROR] Error reading {file_id}: {'; '.join(read_errors)}"}

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
            
    pure_base_id = "_".join(clean_parts)
    
    # 3. Extract Header Row
    header_row_raw = df_filtered.iloc[0]
    header_stats = ["Ids"] + header_row_raw.iloc[1:].tolist()

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
        'skipped': False,
        'file_path': file_path,
        'original_id': file_id_split,
        'pure_base_id': pure_base_id,
        'tags_tuple': tuple(found_meanings), 
        'header_stats': header_stats,
        'extracted_stats': extracted_stats,
        'duration_val': duration_val
    }

def worker_wrapper(args):
    """Helper wrapper for pool.map to pass multiple arguments."""
    return extract_data_from_excel(*args)

def main():
    should_group = False
    user_tags = {}

    # --- 1. Catch variables from Flet via sys.argv ---
    if len(sys.argv) > 1:
        folder_input = sys.argv[1]
        folder_output = sys.argv[2].strip() if len(sys.argv) > 2 and sys.argv[2].strip() else folder_input
        experiment_name = sys.argv[3].strip() if len(sys.argv) > 3 else "experiment"
        
        if len(sys.argv) > 4:
            try:
                user_tags = json.loads(sys.argv[4])
            except Exception:
                user_tags = {}

        if len(sys.argv) > 5:
            should_group = str(sys.argv[5]).strip().lower() in ['y', 'yes', 'true', '1']

        print(f"[START] Running AIO Data Compilation...")
        print(f"[PATH] Input Folder: {folder_input}")
        print(f"[PATH] Output Folder: {folder_output}")
        print(f"[CONFIG] Tags Registered: {user_tags}")
        print(f"[CONFIG] Trial Grouping: {'Enabled (Group Subject ID & Tags)' if should_group else 'Disabled (Keep All Trials)'}\n")

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
        
        folder_output = input('In which folder do you want your excel file to be at: ').strip()
        if folder_output == "":
            print("No input. Saving to same folder as your filtered excel files.")
            folder_output = folder_input
        elif not os.path.isdir(folder_output):
            print('[ERROR] Invalid path input.')
            return
            
        experiment_name = input('What experiment are these files from (footprint, beam, swimming, gridwalk)? ').strip()
        
        print("\n--- DYNAMIC TAG CONFIGURATION ---")
        print("Enter filename tags and their meanings (e.g. Code: F -> Meaning: Female). Enter 'done' when finished.")
        while True:
            code = input("Tag Code (or 'done'): ").strip()
            if code.lower() == 'done':
                break
            meaning = input(f"Meaning for tag '{code}': ").strip()
            if code and meaning:
                user_tags[code] = meaning

        print("\n--- GROUPING CONFIGURATION ---")
        group_choice = input("Do you want to group the means according to Detected IDs & Tags? (y/n): ").strip().lower()
        should_group = group_choice in ['y', 'yes']

    # --- 3. GET FILES ---
    file_paths = sorted([
        os.path.join(folder_input, p) for p in os.listdir(folder_input) 
        if p.lower().endswith('filtered.xlsx') and not p.startswith('~$')
    ])
    if not file_paths:
        print(f"[WARNING] No '*filtered.xlsx' files found in '{folder_input}'.")
        return
    
    total_files = len(file_paths)
    print(f"[INFO] Found {total_files} files. Starting parallel AIO data extraction...")

    # Combine arguments for pool worker
    tasks = [(fp, user_tags) for fp in file_paths]

    # --- PHASE 1: READ MULTIPLE FILES IN PARALLEL ---
    num_cores = max(1, cpu_count() - 2)
    with Pool(processes=num_cores) as pool:
        results = pool.map(worker_wrapper, tasks)

    if should_group:
        print("Data extraction complete! Grouping trials by Subject ID and Identified Tags...\n")
    else:
        print("Data extraction complete! Compiling data without grouping...\n")

    # Determine dynamic tag column headers
    tag_headers = list(dict.fromkeys(user_tags.values())) if user_tags else []

    # --- PHASE 2: WRITE SEQUENTIALLY TO ONE EXCEL FILE ---
    compiled_stats = {sheet: [] for sheet in ["Mean", "Std", "Median", "Min", "Max", "Max_Normalized_Mean", "CV"]}
    compiled_durations = []
    master_header = None

    for res in results:
        if res.get('skipped'):
            continue
        if res.get('error'):
            print(res['error'])
            continue
        
        if master_header is None and res.get('header_stats'):
            base_stat_headers = res['header_stats'][1:] 
            master_header = ["Ids"] + tag_headers + base_stat_headers

        current_id = res['pure_base_id'] if should_group else res['original_id']
        current_tags = list(res['tags_tuple'])

        # Align tag values to match master tag_headers
        tag_values_row = []
        for th in tag_headers:
            if th in current_tags:
                tag_values_row.append(th)
            else:
                tag_values_row.append(np.nan)

        for sheet_name, row_data in res['extracted_stats'].items():
            if sheet_name in compiled_stats:
                compiled_stats[sheet_name].append([current_id] + tag_values_row + row_data)

        if res['duration_val'] is not None:
            compiled_durations.append([current_id] + tag_values_row + [res['duration_val']])

    output_filename = f'{experiment_name.upper()}_AIO_descriptive_statistics.xlsx'
    output_path = os.path.join(folder_output, output_filename)

    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        group_cols = ["Ids"] + tag_headers if should_group else None

        for sheet_name, rows in compiled_stats.items():
            if rows: 
                df = pd.DataFrame(rows, columns=master_header)
                numeric_cols = [c for c in df.columns if c not in ["Ids"] + tag_headers]
                
                df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
                
                if should_group and group_cols:
                    df_final = df.groupby(group_cols, as_index=False, dropna=False)[numeric_cols].mean()
                else:
                    df_final = df
                    
                df_final.to_excel(writer, sheet_name=sheet_name, index=False)

        if compiled_durations:
            duration_headers = ["Ids"] + tag_headers + ["Time Duration"]
            df_duration = pd.DataFrame(compiled_durations, columns=duration_headers)
            df_duration['Time Duration'] = pd.to_numeric(df_duration['Time Duration'], errors='coerce')
            
            if should_group and group_cols:
                df_duration_final = df_duration.groupby(group_cols, as_index=False, dropna=False).mean()
            else:
                df_duration_final = df_duration
                
            df_duration_final.to_excel(writer, sheet_name="Time Duration", index=False)

    print(f"[SUCCESS] AIO Data saved to: {output_path}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nProgram terminated by user. Exiting...')
        sys.exit(0)

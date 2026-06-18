import os
import sys
import re
import json
import pandas as pd
from functools import partial
from multiprocessing import Pool, cpu_count

# --- FIX: Ensure UTF-8 output for Flet UI text box emojis ---
if sys.stdout.encoding is not None and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def extract_data_from_excel(file_path, user_tags):
    """
    WORKER FUNCTION (Runs in parallel)
    Opens a single Excel file, extracts rows, and parses tags dynamically.
    """
    file_id = os.path.basename(file_path)
    
    try:
        df_filtered = pd.read_excel(file_path, sheet_name='Kinematics', header=None)
    except Exception as e:
        return {'error': f"❌ Error reading {file_id}: {e}"}

    parts = file_id.split("_")
    file_id_split = "_".join(parts[:parts.index("out")]) if "out" in parts else file_id

    # 1. Apply the trial number removal
    cleaned_id_str = re.sub(r'_\d{1,2}(?=_)', '', file_id_split, count=1)

    # 2. Extract Tags Dynamically based on user input
    found_meanings = []
    clean_parts = []
    
    # Make tag lookup case-insensitive for robustness
    user_tags_upper = {k.upper(): v for k, v in user_tags.items()}

    for p in cleaned_id_str.split("_"):
        p_upper = p.upper()
        
        # If the filename part matches a user-defined tag, store its meaning
        if p_upper in user_tags_upper:
            found_meanings.append(user_tags_upper[p_upper])
        else:
            # If not a recognized tag, it belongs to the base animal/file ID
            clean_parts.append(p)
            
    # Reassemble the base ID without the parsed tags
    base_id = "_".join(clean_parts)
    
    # Combine found meanings into a single string for the dataset
    tags_joined = " - ".join(found_meanings) if found_meanings else "Uncategorized"
    
    # Generate a warning if no defined tags were found in this file
    warning_msg = None
    if not found_meanings and user_tags:
        warning_msg = f"⚠️ [WARNING] No matching tags found in filename: '{file_id}'. Assumed Base ID: '{base_id}'"

    # 3. Format Headers
    header_row_raw = df_filtered.iloc[0]
    # Replaced hardcoded columns with a single dynamic "Identified Tags" column
    header_stats = ["Ids", "Identified Tags"] + header_row_raw.iloc[1:].tolist()

    # 4. Extract Statistics
    stats_to_extract = {
        "Mean": "Mean", "Std": "Std", "Median": "Median", 
        "Min": "Min", "Max": "Max"
    }
    extracted_stats = {}
    
    for keyword, sheet_name in stats_to_extract.items():
        mask = df_filtered.iloc[:, 0].astype(str).str.contains(keyword, case=False, na=False)
        found_rows = df_filtered[mask]

        if not found_rows.empty:
            stat_values = found_rows.iloc[-1]
            # Attach base_id and tags, then the values
            stat_data = [base_id, tags_joined] + stat_values.iloc[1:].tolist()
            extracted_stats[sheet_name] = stat_data

    # 5. Extract Time Duration
    duration_val = None
    mask_duration = df_filtered.iloc[:, 0].astype(str).str.contains("Duration", case=False, na=False)
    found_duration_rows = df_filtered[mask_duration]
    
    if not found_duration_rows.empty:
        duration_values = found_duration_rows.iloc[-1]
        duration_val = duration_values.iloc[1]

    return {
        'error': None,
        'warning': warning_msg,
        'file_path': file_path,
        'base_id': base_id,
        'tags_joined': tags_joined,
        'header_stats': header_stats,
        'extracted_stats': extracted_stats,
        'duration_val': duration_val
    }

def main():
    user_tags = {}
    
    # --- 1. Catch variables from Flet via sys.argv ---
    if len(sys.argv) > 1:
        folder_input = sys.argv[1]
        folder_output = sys.argv[2].strip() if len(sys.argv) > 2 and sys.argv[2].strip() else folder_input
        experiment_name = sys.argv[3].strip() if len(sys.argv) > 3 else "experiment"
        
        # NEW: Catch the JSON string of tags passed from Flet
        if len(sys.argv) > 4:
            try:
                user_tags = json.loads(sys.argv[4])
            except json.JSONDecodeError:
                print("⚠️ [WARNING] Failed to parse tags from Flet UI. Defaulting to standard parsing.")
        
        print(f"🚀 Running Data Compilation via Flet UI...")
        print(f"📁 Input Folder: {folder_input}")
        print(f"🏷️ Active Tags: {len(user_tags)} defined\n")
        
        if not os.path.isdir(folder_input):
            print(f"❌ [ERROR] The provided input path is not a valid directory: {folder_input}")
            sys.exit(1)

    # --- 2. Fallback to terminal inputs if run manually ---
    else:
        folder_input = input('Which folder has your filtered xlsx files? ').strip()
        if not os.path.isdir(folder_input):
            print('❌ Invalid path input.')
            return
        folder_output = input('In which folder do you want your excel file to be at (leave blank for same as input): ').strip()
        folder_output = folder_output if folder_output else folder_input
        experiment_name = input('What experiment are these files from? ').strip()
        print("ℹ️ Running in manual mode. Dynamic tags are disabled.")

    # --- 3. GET FILES ---
    file_paths = [os.path.join(folder_input, p) for p in os.listdir(folder_input) if p.endswith('filtered.xlsx')]
    if not file_paths:
       print(f"⚠️ No '_filtered.xlsx' files found in the folder '{folder_input}'.")
       return
    
    total_files = len(file_paths)
    print(f"⚙️ Found {total_files} files. Starting parallel data extraction...\n")

    # --- PHASE 1: READ MULTIPLE FILES IN PARALLEL ---
    num_cores = max(1, cpu_count() - 2) 
    
    # NEW: Bind the user_tags dictionary to the worker function so Pool.map can use it
    worker_func = partial(extract_data_from_excel, user_tags=user_tags)
    
    with Pool(processes=num_cores) as pool:
        results = pool.map(worker_func, file_paths)

    print("\n✅ Data extraction complete! Formatting data...")

    # --- PHASE 2: WRITE SEQUENTIALLY TO ONE EXCEL FILE ---
    compiled_stats = {sheet: [] for sheet in ["Mean", "Std", "Median", "Min", "Max"]}
    compiled_durations = []
    master_header = None

    for res in results:
        # Check for errors and warnings returned from workers
        if res['error']:
            print(res['error'])
            continue 
        if res['warning']:
            print(res['warning'])
            
        if master_header is None and res['header_stats']:
            master_header = res['header_stats']

        for sheet_name, row_data in res['extracted_stats'].items():
            compiled_stats[sheet_name].append(row_data)

        if res['duration_val'] is not None:
            # Include the tags in the duration dataset too!
            compiled_durations.append([res['base_id'], res['tags_joined'], res['duration_val']])

    sample_path_split = os.path.normpath(file_paths[0]).split(os.path.sep)
    dir_part_1 = sample_path_split[-3] if len(sample_path_split) >= 3 else "folder"
    dir_part_2 = sample_path_split[-2] if len(sample_path_split) >= 2 else "output"
    
    output_filename = f'{experiment_name.upper()}_descriptive_statistics_{dir_part_1}_{dir_part_2}.xlsx'
    output_path = os.path.join(folder_output, output_filename)

    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        
        # 1. Write the stat sheets
        for sheet_name, rows in compiled_stats.items():
            if rows:
                df = pd.DataFrame(rows, columns=master_header)
                
                # NEW LOGIC: Exclude BOTH string columns before calculating the mean
                numeric_cols = df.columns.drop(['Ids', 'Identified Tags'])
                df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
                
                # Group by BOTH Ids and Tags to preserve the tags in the final averaged sheet
                df_grouped = df.groupby(['Ids', 'Identified Tags'], as_index=False)[numeric_cols].mean()
                df_grouped.to_excel(writer, sheet_name=sheet_name, index=False)

        # 2. Write the Time Duration sheet
        if compiled_durations:
            df_duration = pd.DataFrame(compiled_durations, columns=["Ids", "Identified Tags", "Time Duration"])
            df_duration['Time Duration'] = pd.to_numeric(df_duration['Time Duration'], errors='coerce')
            
            # Group by BOTH to preserve tags
            df_duration_grouped = df_duration.groupby(['Ids', 'Identified Tags'], as_index=False).mean()
            df_duration_grouped.to_excel(writer, sheet_name="Time Duration", index=False)

    print(f"\n🎉 Success! Data averaged across trials and saved to:\n➡️ {output_filename}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n👋 Program terminated by user. Exiting function...')
        sys.exit(0)
import os
import sys
import re
import pandas as pd
from multiprocessing import Pool, cpu_count

# --- FIX: Ensure UTF-8 output for Flet UI text box emojis ---
# if sys.stdout.encoding is not None and sys.stdout.encoding.lower() != 'utf-8':
#     sys.stdout.reconfigure(encoding='utf-8')

def extract_data_from_excel(file_path):
    """
    WORKER FUNCTION (Runs in parallel)
    Opens a single Excel file, extracts the needed rows, and returns a dictionary.
    """
    file_id = os.path.basename(file_path)
    
    try:
        # calamine is extremely fast for reading Excel
        df_filtered = pd.read_excel(file_path, sheet_name='Kinematics', header=None, engine='calamine')
    except Exception as e:
        error_msg = f"❌ Error reading {file_id}: {e}"
        print(error_msg) 
        return {'error': error_msg}

    parts = file_id.split("_")
    file_id_split = "_".join(parts[:parts.index("out")]) if "out" in parts else file_id
    
    # NEW: Remove trailing trial numbers (e.g., "_01", "_02") to get the base subject ID
    # This looks for an underscore followed by digits at the end of the string
    #base_id = re.sub(r'_\d+$', '', file_id_split) THIS WORKS FOR MY FILE NAMES NOT FOR INES
    # Removes a 1 or 2-digit number surrounded by underscores from the string
    base_id = re.sub(r'_\d{1,2}(?=_)', '', file_id_split, count=1) # THIS WORKS FOR BROADER NAMING CONVENTIONS IN SOME FILENAMES

    # 1. Extract the Header Row
    header_row_raw = df_filtered.iloc[0]
    header_stats = ["Ids"] + header_row_raw.iloc[1:].tolist()

    # OPTIMIZATION: Convert the label column to lowercase strings ONCE instead of inside the loop
    first_col = df_filtered.iloc[:, 0].astype(str).str.lower()

    # 2. Extract Statistics
    stats_to_extract = {
        "mean": "Mean", "std": "Std", "median": "Median", 
        "min": "Min", "max": "Max"
    }
    extracted_stats = {}
    
    for keyword, sheet_name in stats_to_extract.items():
        # Searching is faster since first_col is already lowercased and string-cast
        mask = first_col.str.contains(keyword, na=False)
        found_rows = df_filtered[mask]

        if not found_rows.empty:
            stat_values = found_rows.iloc[-1]
            # Use base_id so trials share the same identifier
            stat_data = [base_id] + stat_values.iloc[1:].tolist()
            extracted_stats[sheet_name] = stat_data

    # 3. Extract Time Duration
    duration_val = None
    mask_duration = first_col.str.contains("duration", na=False)
    found_duration_rows = df_filtered[mask_duration]
    
    if not found_duration_rows.empty:
        duration_values = found_duration_rows.iloc[-1]
        duration_val = duration_values.iloc[1]

    print(f"📄 Extracted data from: {file_id}")

    return {
        'error': None,
        'file_path': file_path,
        'base_id': base_id, # Replaced file_id_split with base_id
        'header_stats': header_stats,
        'extracted_stats': extracted_stats,
        'duration_val': duration_val
    }

def main():
    # --- 1. Catch variables from Flet via sys.argv ---
    if len(sys.argv) > 1:
        folder_input = sys.argv[1]
        folder_output = sys.argv[2].strip() if len(sys.argv) > 2 and sys.argv[2].strip() else folder_input
        experiment_name = sys.argv[3].strip() if len(sys.argv) > 3 else "experiment"
        
        print(f"🚀 Running Data Compilation via Flet UI...")
        print(f"📁 Input Folder: {folder_input}")
        print(f"📁 Output Folder: {folder_output}")
        print(f"🔬 Experiment: {experiment_name.upper()}\n")
        
        if not os.path.isdir(folder_input):
            print(f"❌ [ERROR] The provided input path is not a valid directory: {folder_input}")
            sys.exit(1)
            
        if not os.path.isdir(folder_output):
            print(f"❌ [ERROR] The provided output path is not a valid directory: {folder_output}")
            sys.exit(1)

    # --- 2. Fallback to terminal inputs if run manually ---
    else:
        folder_input = input('Which folder has your filtered xlsx files? ').strip()
        if not os.path.isdir(folder_input):
            print('❌ Invalid path input.')
            return
        
        folder_output = input('In which folder do you want your excel file to be at (leave blank for same as input): ').strip()
        if folder_output == "":
            print("ℹ️ No input. Saving to same folder as your filtered excel files")
            folder_output = folder_input
        elif not os.path.isdir(folder_output):
            print('❌ Invalid path input.')
            return
            
        experiment_name = input('What experiment are these files from (footprint, beam, swimming, gridwalk)? ').strip()

    # --- 3. GET FILES ---
    file_paths = [os.path.join(folder_input, p) for p in os.listdir(folder_input) if p.endswith('filtered.xlsx')]
    if not file_paths:
       print(f"⚠️ No '_filtered.xlsx' files found in the folder '{folder_input}'.")
       return
    
    total_files = len(file_paths)
    print(f"⚙️ Found {total_files} files. Starting parallel data extraction...\n")

    # --- PHASE 1: READ MULTIPLE FILES IN PARALLEL ---
    # Reserving 1 or 2 cores is usually enough. This ensures at least 1 core runs the task, 
    # but prevents standard 4-core laptops from dropping to a single-threaded bottleneck.
    num_cores = max(1, cpu_count() - 2) 
    
    with Pool(processes=num_cores) as pool:
        results = pool.map(extract_data_from_excel, file_paths)

    print("\n✅ Data extraction complete! Grouping trials and writing to Excel...")

    # --- PHASE 2: WRITE SEQUENTIALLY TO ONE EXCEL FILE ---
    compiled_stats = {sheet: [] for sheet in ["Mean", "Std", "Median", "Min", "Max"]}
    compiled_durations = []
    master_header = None

    for res in results:
        if res['error']:
            continue 
        
        if master_header is None and res['header_stats']:
            master_header = res['header_stats']

        for sheet_name, row_data in res['extracted_stats'].items():
            compiled_stats[sheet_name].append(row_data)

        if res['duration_val'] is not None:
            compiled_durations.append([res['base_id'], res['duration_val']])

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
                
                # NEW LOGIC: Convert to numeric, group by 'Ids', and calculate the mean
                numeric_cols = df.columns.drop('Ids')
                df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
                df_grouped = df.groupby('Ids', as_index=False)[numeric_cols].mean()
                
                df_grouped.to_excel(writer, sheet_name=sheet_name, index=False)

        # 2. Write the Time Duration sheet
        if compiled_durations:
            df_duration = pd.DataFrame(compiled_durations, columns=["Ids", "Time Duration"])
            
            # NEW LOGIC: Convert duration to numeric and group by ID to get the mean
            df_duration['Time Duration'] = pd.to_numeric(df_duration['Time Duration'], errors='coerce')
            df_duration_grouped = df_duration.groupby('Ids', as_index=False).mean()
            
            df_duration_grouped.to_excel(writer, sheet_name="Time Duration", index=False)

    print(f"\n🎉 Success! Data averaged across trials and saved to:\n➡️ {output_filename}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n👋 Program terminated by user. Exiting function...')
        sys.exit(0)
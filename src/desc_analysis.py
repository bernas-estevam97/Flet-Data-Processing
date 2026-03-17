import os
import sys
import pandas as pd
from multiprocessing import Pool, cpu_count

# --- FIX: Ensure UTF-8 output for Flet UI text box emojis ---
# if sys.stdout.encoding is not None and sys.stdout.encoding.lower() != 'utf-8':
#     sys.stdout.reconfigure(encoding='utf-8')

# Removed the deprecated pd.set_option line that was causing the warning

def extract_data_from_excel(file_path):
    """
    WORKER FUNCTION (Runs in parallel)
    Opens a single Excel file, extracts the needed rows, and returns a dictionary.
    """
    file_id = os.path.basename(file_path)
    
    try:
        df_filtered = pd.read_excel(file_path, sheet_name='Kinematics', header=None, engine='calamine')
    except Exception as e:
        error_msg = f"❌ Error reading {file_id}: {e}"
        print(error_msg) 
        return {'error': error_msg}

    parts = file_id.split("_")
    file_id_split = "_".join(parts[:parts.index("out")]) if "out" in parts else file_id

    # 1. Extract the Header Row
    header_row_raw = df_filtered.iloc[0]
    header_stats = ["Ids"] + header_row_raw.iloc[1:].tolist()

    # 2. Extract Statistics
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
            stat_data = [file_id_split] + stat_values.iloc[1:].tolist()
            extracted_stats[sheet_name] = stat_data

    # 3. Extract Time Duration
    duration_val = None
    mask_duration = df_filtered.iloc[:, 0].astype(str).str.contains("Duration", case=False, na=False)
    found_duration_rows = df_filtered[mask_duration]
    
    if not found_duration_rows.empty:
        duration_values = found_duration_rows.iloc[-1]
        duration_val = duration_values.iloc[1]

    print(f"📄 Extracted data from: {file_id}")

    return {
        'error': None,
        'file_path': file_path,
        'file_id_split': file_id_split,
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
    num_cores = max(1, cpu_count() - 1) 
    
    with Pool(processes=num_cores) as pool:
        results = pool.map(extract_data_from_excel, file_paths)

    print("\n✅ Data extraction complete! Formatting and writing to Excel...")

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
            compiled_durations.append([res['file_id_split'], res['duration_val']])

    sample_path_split = os.path.normpath(file_paths[0]).split(os.path.sep)
    dir_part_1 = sample_path_split[-3] if len(sample_path_split) >= 3 else "folder"
    dir_part_2 = sample_path_split[-2] if len(sample_path_split) >= 2 else "output"
    
    output_filename = f'{experiment_name.upper()}_descriptive_statistics_{dir_part_1}_{dir_part_2}.xlsx'
    output_path = os.path.join(folder_output, output_filename)

    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        
        # 1. Write the stat sheets
        for sheet_name, rows in compiled_stats.items():
            if rows:
                # Add infer_objects to securely type cast without silent downcasting warnings
                df = pd.DataFrame(rows, columns=master_header).infer_objects()
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        # 2. Write the Time Duration sheet
        if compiled_durations:
            df_duration = pd.DataFrame(compiled_durations, columns=["Ids", "Time Duration"]).infer_objects()
            df_duration.to_excel(writer, sheet_name="Time Duration", index=False)

    print(f"\n🎉 Success! Data perfectly ordered and saved to:\n➡️ {output_filename}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n👋 Program terminated by user. Exiting function...')
        sys.exit(0)
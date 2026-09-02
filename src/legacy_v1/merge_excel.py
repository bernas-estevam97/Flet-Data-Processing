import sys
import os
import pandas as pd

def main():
    # Expecting at least 4 arguments: script.py <file1> <file2> ... <out_folder> <out_filename>
    # sys.argv[0] is the script name.
    if len(sys.argv) < 4:
        print("[ERROR] Insufficient arguments passed to script.")
        print("Expected: script.py <file1> ... <fileN> <out_folder> <out_filename>")
        sys.exit(1)
    
    # Extract outputs from the end of the argument list
    out_filename = sys.argv[-1]
    out_folder = sys.argv[-2]
    
    # Extract all input files (everything between the script name and the output folder)
    input_files = sys.argv[1:-2]

    # Ensure the filename ends with .xlsx
    if not out_filename.endswith('.xlsx'):
        out_filename += '.xlsx'
        
    output_path = os.path.join(out_folder, out_filename)

    print(f"Output will be saved to: {output_path}")
    print(f"Files to merge ({len(input_files)}):")

    # 1. Read all files into a list of dictionaries
    all_file_dicts = []
    for file_path in input_files:
        print(f" - Reading: {os.path.basename(file_path)}")
        try:
            file_dict = pd.read_excel(file_path, sheet_name=None)
            all_file_dicts.append(file_dict)
        except Exception as e:
            print(f"[ERROR] Failed to read {os.path.basename(file_path)}. {e}")
            sys.exit(1)

    # 2. Get a unique set of all sheet names across ALL provided files
    all_sheets = set()
    for file_dict in all_file_dicts:
        all_sheets.update(file_dict.keys())
    
    # 3. Merge and save
    try:
        print("Merging sheets vertically...")
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet in all_sheets:
                # Gather the dataframe for 'sheet' from every file
                dfs_to_concat = []
                for file_dict in all_file_dicts:
                    df = file_dict.get(sheet, pd.DataFrame())
                    dfs_to_concat.append(df)
                
                # Concatenate them all at once
                merged_df = pd.concat(dfs_to_concat, ignore_index=True)
                merged_df.to_excel(writer, sheet_name=sheet, index=False)
                print(f" - Sheet processed: {sheet}")
        
        print(f"Success! Merged file saved to:")
        print(f"{output_path}")
    except Exception as e:
        print(f"[ERROR] Failed to save merged file. {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
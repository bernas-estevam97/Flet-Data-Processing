import sys
import os
import pandas as pd

def main():
    # Expecting: script.py <file1> <file2> <out_folder> <out_filename>
    if len(sys.argv) != 5:
        print("[ERROR] Incorrect number of arguments passed to script.")
        sys.exit(1)
    
    file1_path = sys.argv[1]
    file2_path = sys.argv[2]
    out_folder = sys.argv[3]
    out_filename = sys.argv[4]

    # Ensure the filename ends with .xlsx
    if not out_filename.endswith('.xlsx'):
        out_filename += '.xlsx'
        
    output_path = os.path.join(out_folder, out_filename)

    print(f"Reading File 1: {os.path.basename(file1_path)}")
    print(f"Reading File 2: {os.path.basename(file2_path)}")

    try:
        dict1 = pd.read_excel(file1_path, sheet_name=None)
        dict2 = pd.read_excel(file2_path, sheet_name=None)
    except Exception as e:
        print(f"[ERROR] Failed to read Excel files. {e}")
        sys.exit(1)

    all_sheets = set(dict1.keys()).union(set(dict2.keys()))
    
    try:
        print("Merging sheets vertically...")
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet in all_sheets:
                df1 = dict1.get(sheet, pd.DataFrame())
                df2 = dict2.get(sheet, pd.DataFrame())
                
                merged_df = pd.concat([df1, df2], ignore_index=True)
                merged_df.to_excel(writer, sheet_name=sheet, index=False)
                print(f" - Sheet processed: {sheet}")
        
        print(f"Success! Merged file saved to:")
        print(f"{output_path}")
    except Exception as e:
        print(f"[ERROR] Failed to save merged file. {e}")
        sys.exit(1)

if __name__ == '__main__':
    # Disable silent downcasting warning if pandas version triggers it
    pd.set_option('future.no_silent_downcasting', True)
    main()
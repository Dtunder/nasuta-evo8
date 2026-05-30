import os
import pandas as pd
from pathlib import Path

def find_excel_files(directories):
    files = []
    for d in directories:
        p = Path(d)
        if p.exists() and p.is_dir():
            files.extend(list(p.rglob("*.xlsx")))
    return files

def main():
    directories_to_search = ['evo10', 'evo10_collected']
    excel_files = find_excel_files(directories_to_search)

    # We only want to save to master_all.xlsx, so exclude it from being read
    master_file_name = 'master_all.xlsx'

    all_dfs = []

    for f in excel_files:
        if f.name == master_file_name:
            continue
        try:
            df = pd.read_excel(f)
            # check if it has seed and rounds_survived
            if 'seed' in df.columns and 'rounds_survived' in df.columns:
                df['source'] = f.name
                all_dfs.append(df)
            else:
                print(f"Skipping {f.name} - missing required columns.")
        except Exception as e:
            print(f"Error reading {f}: {e}")

    if not all_dfs:
        print("No valid data found.")
        # create an empty master file
        df_all = pd.DataFrame(columns=['source', 'seed', 'rounds_survived'])
        df_summary = pd.DataFrame(columns=['source', 'mean_rounds_survived', 'max_rounds_survived', 'count'])
    else:
        df_all = pd.concat(all_dfs, ignore_index=True)
        # We need to keep all rows that have columns seed/rounds_survived into one big DataFrame.
        # Ensure 'rounds_survived' is numeric
        df_all['rounds_survived'] = pd.to_numeric(df_all['rounds_survived'], errors='coerce')

        # calculate summary
        summary = df_all.groupby('source').agg(
            mean_rounds_survived=('rounds_survived', 'mean'),
            max_rounds_survived=('rounds_survived', 'max'),
            count=('rounds_survived', 'count')
        ).reset_index()

        df_summary = summary

    master_path = Path('evo10/master/master_all.xlsx')
    master_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(master_path, engine='openpyxl') as writer:
        df_all.to_excel(writer, sheet_name='all', index=False)
        df_summary.to_excel(writer, sheet_name='summary', index=False)

    print(f"Saved master file to {master_path}")

if __name__ == '__main__':
    main()

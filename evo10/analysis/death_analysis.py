import pandas as pd
import os

def main():
    target_dirs = ['evo10', 'evo10_collected']
    all_files = []

    for d in target_dirs:
        if os.path.exists(d):
            for root, _, files in os.walk(d):
                for f in files:
                    if f.endswith('.xlsx') or f.endswith('.csv'):
                        all_files.append(os.path.join(root, f))

    combined_data = []

    for f in all_files:
        try:
            if f.endswith('.xlsx'):
                df = pd.read_excel(f)
            else:
                df = pd.read_csv(f)

            if 'death_cause' in df.columns:
                # keep only the death_cause column to save memory, or maybe also model/source if available
                # The prompt says "split by mode/source if available" - maybe it means group by it?
                # Actually it says: "count how often each death_cause occurs, split by mode/source if available."

                # Let's check if 'mode' or 'source' is in columns
                cols_to_keep = ['death_cause']
                if 'mode' in df.columns:
                    cols_to_keep.append('mode')
                if 'source' in df.columns:
                    cols_to_keep.append('source')

                combined_data.append(df[cols_to_keep])
        except Exception as e:
            print(f"Failed to read {f}: {e}")

    if not combined_data:
        print("No files with 'death_cause' found.")
        os.makedirs('evo10/analysis', exist_ok=True)
        pd.DataFrame(columns=['death_cause', 'count']).to_excel('evo10/analysis/death_causes.xlsx', sheet_name='counts', index=False)
        with open('evo10/analysis/death_summary.txt', 'w') as f:
            f.write("No data found.\n")
        return

    combined_df = pd.concat(combined_data, ignore_index=True)

    # We need to count how often each death_cause occurs, split by mode/source if available.
    # Group by all available columns in combined_data
    group_cols = ['death_cause']
    if 'mode' in combined_df.columns:
        group_cols.append('mode')
    if 'source' in combined_df.columns:
        group_cols.append('source')

    # Drop NAs in death_cause just to be clean
    combined_df = combined_df.dropna(subset=['death_cause'])

    counts = combined_df.groupby(group_cols).size().reset_index(name='count')
    # Sort descending by count
    counts = counts.sort_values(by='count', ascending=False)

    os.makedirs('evo10/analysis', exist_ok=True)

    counts.to_excel('evo10/analysis/death_causes.xlsx', sheet_name='counts', index=False)

    # Top 3 death causes overall
    top_overall = combined_df['death_cause'].value_counts().head(3)

    with open('evo10/analysis/death_summary.txt', 'w') as f:
        f.write("Top 3 Death Causes:\n")
        for cause, count in top_overall.items():
            f.write(f"{cause}: {count}\n")

    print("Analysis complete. Saved to evo10/analysis/death_causes.xlsx and death_summary.txt")

if __name__ == '__main__':
    main()

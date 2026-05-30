import os
import glob
import pandas as pd

def main():
    logs_dir = "evo10/logs"
    output_path = "evo10/runs/all_results.xlsx"

    # Find all matching CSV files
    csv_files = glob.glob(os.path.join(logs_dir, "multiseed_raw_*.csv"))

    if not csv_files:
        print(f"No CSV files found in {logs_dir}")
        return

    # Read and concatenate
    dfs = []
    for f in csv_files:
        df = pd.read_csv(f)
        dfs.append(df)

    combined_df = pd.concat(dfs, ignore_index=True)

    # Create summary
    summary_df = combined_df.groupby("model")["rounds_survived"].agg(["mean", "count"]).reset_index()

    # Write to Excel
    with pd.ExcelWriter(output_path) as writer:
        combined_df.to_excel(writer, sheet_name="raw_data", index=False)
        summary_df.to_excel(writer, sheet_name="summary", index=False)

    print(f"Successfully combined {len(csv_files)} CSVs into {output_path}")

if __name__ == "__main__":
    main()

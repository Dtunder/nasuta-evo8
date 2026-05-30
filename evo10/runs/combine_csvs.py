import glob
import os
import pandas as pd

def main():
    logs_dir = os.path.join("evo10", "logs")
    runs_dir = os.path.join("evo10", "runs")
    output_file = os.path.join(runs_dir, "all_results.xlsx")

    # Ensure runs directory exists
    os.makedirs(runs_dir, exist_ok=True)

    # Find all multiseed_raw_*.csv files
    pattern = os.path.join(logs_dir, "multiseed_raw_*.csv")
    csv_files = glob.glob(pattern)

    if not csv_files:
        print(f"No CSV files found matching {pattern}")
        return

    # Read and concatenate all CSV files
    dfs = []
    for f in csv_files:
        df = pd.read_csv(f)
        dfs.append(df)

    combined_df = pd.concat(dfs, ignore_index=True)

    # Group by model and calculate summary statistics
    summary_df = combined_df.groupby("model").agg(
        count=("model", "count"),
        mean_rounds_survived=("rounds_survived", "mean")
    ).reset_index()

    # Save to Excel with two sheets
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        combined_df.to_excel(writer, sheet_name="data", index=False)
        summary_df.to_excel(writer, sheet_name="summary", index=False)

    print(f"Successfully combined {len(csv_files)} CSV files into {output_file}")

if __name__ == "__main__":
    main()

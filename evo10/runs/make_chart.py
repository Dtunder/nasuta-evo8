import pandas as pd
import glob
import os

def main():
    # Find all matching CSV files
    csv_files = glob.glob('evo10/logs/multiseed_raw_*.csv')

    if not csv_files:
        print("No CSV files found.")
        return

    # Read and concatenate all CSV files
    df_list = [pd.read_csv(f) for f in csv_files]
    df = pd.concat(df_list, ignore_index=True)

    # Calculate average rounds_survived per model
    df_by_model = df.groupby('model')['rounds_survived'].mean().reset_index()

    # Write to Excel
    output_path = 'evo10/runs/comparison.xlsx'
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='data', index=False)
        df_by_model.to_excel(writer, sheet_name='by_model', index=False)

    print(f"Created {output_path} successfully.")

if __name__ == "__main__":
    main()

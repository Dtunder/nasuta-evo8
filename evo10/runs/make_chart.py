import pandas as pd
import glob
import os

def main():
    # Find all multiseed_raw_*.csv files
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    csv_files = glob.glob(os.path.join(log_dir, 'multiseed_raw_*.csv'))

    if not csv_files:
        print("No csv files found.")
        return

    # Read and concatenate all csv files
    df_list = [pd.read_csv(f) for f in csv_files]
    df = pd.concat(df_list, ignore_index=True)

    # Calculate average rounds_survived per model
    by_model_df = df.groupby('model')['rounds_survived'].mean().reset_index()

    # Write to Excel
    output_path = os.path.join(os.path.dirname(__file__), 'comparison.xlsx')
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='data', index=False)
        by_model_df.to_excel(writer, sheet_name='by_model', index=False)

    print(f"Excel file created at {output_path}")

if __name__ == "__main__":
    main()

import os
import glob
import csv
import math
import numpy as np

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(ROOT_DIR, "logs")

def main():
    print("--- Consolidating Parallel Multiseed Results ---")
    pattern = os.path.join(LOG_DIR, "multiseed_raw_*.csv")
    csv_files = glob.glob(pattern)
    
    if not csv_files:
        print("No parallel multiseed raw CSV files found!")
        return
        
    print(f"Found {len(csv_files)} files: {[os.path.basename(f) for f in csv_files]}")
    
    all_results = []
    for filepath in csv_files:
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                all_results.append({
                    'model': row['model'],
                    'seed': int(row['seed']),
                    'rounds_survived': int(row['rounds_survived']),
                    'stability': float(row['stability']),
                    'death_cause': row['death_cause']
                })
                
    # Sort by model and seed
    all_results.sort(key=lambda x: (x['model'], x['seed']))
    
    # Save combined raw data
    combined_csv = os.path.join(LOG_DIR, "multiseed_raw.csv")
    with open(combined_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['model', 'seed', 'rounds_survived', 'stability', 'death_cause'])
        writer.writeheader()
        writer.writerows(all_results)
    print(f"Combined raw data saved to: {combined_csv}")
    
    # Generate Summary Markdown
    summary_md = os.path.join(LOG_DIR, "multiseed_summary.md")
    report = ["# Oekolopoly Sovereign Death Benchmark - Multi-Seed Summary\n"]
    report.append(f"Generated at: {np.datetime64('now').astype(str)} (Consolidated)\n")
    report.append("| Mode | n | Mean Rounds ± CI 95% | Survival Rate | Mean Stability | Dominant Death Cause |")
    report.append("| :--- | :-: | :--- | :--- | :--- | :--- |")
    
    for mode_label in ["Paper", "Sovereign"]:
        mode_data = [r for r in all_results if r['model'] == mode_label]
        n = len(mode_data)
        if n == 0:
            continue
            
        rounds = [r['rounds_survived'] for r in mode_data]
        stabs = [r['stability'] for r in mode_data]
        
        mean_r = np.mean(rounds)
        std_r = np.std(rounds)
        ci_r = 1.96 * std_r / math.sqrt(n) if n > 0 else 0
        
        survival_rate = (sum(1 for r in mode_data if r['rounds_survived'] >= 30) / n) * 100
        mean_s = np.mean(stabs)
        
        death_causes = [r['death_cause'] for r in mode_data if r['death_cause'] != 'survived_30']
        if death_causes:
            from collections import Counter
            dominant_death = Counter(death_causes).most_common(1)[0][0]
        else:
            dominant_death = "None"
            
        report.append(f"| {mode_label} | {n} | {mean_r:.2f} ± {ci_r:.2f} | {survival_rate:.1f}% | {mean_s:.2f} | {dominant_death} |")
        
    with open(summary_md, 'w') as f:
        f.write("\n".join(report) + "\n")
    
    print("\nSummary Table:")
    print("\n".join(report[2:]))
    print(f"\nSummary report saved to: {summary_md}")

if __name__ == "__main__":
    main()

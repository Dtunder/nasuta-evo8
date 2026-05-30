import os
import sys
import numpy as np
import pandas as pd
import math
from collections import Counter
import openpyxl
from openpyxl.styles import Font

# Add paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NASUTA_ROOT = os.path.join(ROOT_DIR, "engine")
SRC_ROOT = os.path.join(ROOT_DIR, "src")

for p in [NASUTA_ROOT, SRC_ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

from oeko_core.envs.oeko_env import OekoEnv

def _metrics_from_V(inner):
    final_V = inner.V
    rounds_survived = int(final_V[8])
    stability = 30 - (np.max(final_V[:8]) - np.min(final_V[:8]))

    di = (getattr(inner, 'done_info', '') or '')
    dtl = getattr(inner, 'dtl', {})
    etl = getattr(inner, 'etl', {})
    th = etl.get(' too high. ')
    too_high = bool(th) and di.endswith(th)

    def _starts(d, key):
        prefix = d.get(key)
        return bool(prefix) and di.startswith(prefix)

    if di.startswith('Maximum number of rounds'):
        death_cause = 'survived'
    elif _starts(dtl, 'Politics'):
        death_cause = 'politics_collapse'
    elif _starts(dtl, 'EnvirDamage'):
        death_cause = 'env_collapse'
    elif _starts(dtl, 'Population'):
        death_cause = 'overpopulation' if too_high else 'extinction'
    elif _starts(dtl, 'ReproRate'):
        death_cause = 'reprorate_collapse'
    elif _starts(dtl, 'QualityOfLife'):
        death_cause = 'quality_of_life_collapse'
    elif _starts(dtl, 'Enlightenment'):
        death_cause = 'education_collapse'
    elif _starts(dtl, 'Production'):
        death_cause = 'production_collapse'
    elif _starts(dtl, 'Redevelop'):
        death_cause = 'sanitation_collapse'
    elif _starts(etl, 'NumAPointsTooLow') or _starts(etl, 'NumAPointsTooHigh'):
        death_cause = 'ap_out_of_range'
    else:
        death_cause = 'unknown'

    return {
        'rounds_survived': rounds_survived,
        'stability': float(stability),
        'death_cause': death_cause
    }

def run_heuristic(seed):
    env = OekoEnv(render_mode=None)
    env.reset(seed=seed)

    for _ in range(60):
        if env.done:
            break

        V = env.V
        V_before_ap = int(V[9])
        ap = int(V[9])
        dist = np.zeros(5, int)

        # Fill Education: min(ap, 29 - V[2])
        d = min(ap, 29 - int(V[2]))
        dist[2] += d
        ap -= d

        # Target Production toward 13
        target_prod = 13
        curr_prod = int(V[1])
        diff = target_prod - curr_prod - dist[1]

        change = min(max(1, ap // 2), abs(13 - int(V[1]) - dist[1]))
        if diff != 0:
            direction = 1 if diff > 0 else -1
            dist[1] += direction * change
            ap -= abs(change)

        # Burn loop
        while ap + V_before_ap > 28:
            if V[2] + dist[2] < 29:
                dist[2] += 1
                ap -= 1
            elif V[3] + dist[3] < 18:
                dist[3] += 1
                ap -= 1
            elif V[4] + dist[4] < 15:
                dist[4] += 1
                ap -= 1
            elif V[1] + dist[1] > 5:
                dist[1] -= 1
                ap -= 1
            else:
                break

        act = np.zeros(6, dtype=np.int64)
        act[:5] = dist

        # Population: act[5]=-4 if V[6]>32 elif V[6]<18 then 5 else 0
        if V[6] > 32:
            act[5] = -4
        elif V[6] < 18:
            act[5] = 5
        else:
            act[5] = 0

        env.unwrapped.step(act - env.unwrapped.Amin)

    metrics = _metrics_from_V(env.unwrapped)
    return {
        'model': 'Heuristic',
        'seed': seed,
        'rounds_survived': metrics['rounds_survived'],
        'stability': metrics['stability'],
        'death_cause': metrics['death_cause']
    }

def main():
    heuristic_results = []
    print("Running Heuristic...")
    for seed in range(30):
        res = run_heuristic(seed)
        heuristic_results.append(res)

    out_dir = os.path.join(ROOT_DIR, "evo10", "heuristic")
    os.makedirs(out_dir, exist_ok=True)

    raw_csv = os.path.join(out_dir, "heuristic_raw_0_29.csv")
    df_heu = pd.DataFrame(heuristic_results)
    df_heu.to_csv(raw_csv, index=False)
    print(f"Saved {raw_csv}")

    # Load Paper and Sovereign results from logs
    log_dir = os.path.join(ROOT_DIR, "evo10", "logs")
    csv_files = [
        "multiseed_raw_0_10.csv",
        "multiseed_raw_10_15.csv",
        "multiseed_raw_15_20.csv",
        "multiseed_raw_25_30.csv"
    ]

    df_logs = []
    for f in csv_files:
        p = os.path.join(log_dir, f)
        if os.path.exists(p):
            df_logs.append(pd.read_csv(p))

    if df_logs:
        df_all = pd.concat(df_logs, ignore_index=True)
    else:
        df_all = pd.DataFrame(columns=['model', 'seed', 'rounds_survived', 'stability', 'death_cause'])

    # We only care about Paper and Sovereign for the summary
    df_all = pd.concat([df_all, df_heu], ignore_index=True)

    summary_data = []
    for model in ["Paper", "Sovereign", "Heuristic"]:
        d = df_all[df_all['model'] == model]
        n = len(d)
        if n > 0:
            mean_r = d['rounds_survived'].mean()
            ci95_r = 1.96 * d['rounds_survived'].std() / math.sqrt(n) if n > 1 else 0.0
            surv_pct = (len(d[d['death_cause'] == 'survived']) / n) * 100
            causes = [c for c in d['death_cause'] if c != 'survived']
            dominant = Counter(causes).most_common(1)[0][0] if causes else "None"
        else:
            mean_r, ci95_r, surv_pct, dominant = 0, 0, 0, "None"

        summary_data.append({
            'model': model,
            'n': n,
            'mean_rounds': mean_r,
            'ci95': ci95_r,
            'survival_rate_pct': surv_pct,
            'dominant_death': dominant
        })

    df_summary = pd.DataFrame(summary_data)

    excel_path = os.path.join(out_dir, "evo10_threeway.xlsx")
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df_summary.to_excel(writer, sheet_name="summary", index=False)

    # Bold headers
    wb = openpyxl.load_workbook(excel_path)
    ws = wb["summary"]
    for cell in ws[1]:
        cell.font = Font(bold=True)
    wb.save(excel_path)

    print(f"Saved {excel_path}")

if __name__ == "__main__":
    main()

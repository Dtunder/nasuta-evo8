import os
import sys
import numpy as np
import random
import csv
import math
import time
import pandas as pd

# Add paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NASUTA_ROOT = os.path.join(ROOT_DIR, "engine")
SRC_ROOT = os.path.join(ROOT_DIR, "src")

for p in [NASUTA_ROOT, SRC_ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

from xai_multiseed import run_once
from oeko_core.envs.oeko_env import OekoEnv

# Dynamic patch to allow 60 rounds
original_inner_step = OekoEnv._OekoEnv__inner_step
def patched_inner_step(self, action, clipping=True):
    real_round = self.V[self.ROUND]
    if real_round >= 30:
        self.V[self.ROUND] = 29
    obs, r, done, trunc, info = original_inner_step(self, action, clipping)
    if real_round >= 30:
        self.V[self.ROUND] = real_round + 1
    if self.V[self.ROUND] >= 60 and not self.done:
        self.done = True
        self.done_info = 'Maximum number of rounds reached.'
        info['done_reason'] = self.done_info
    return obs, r, self.done, trunc, info
OekoEnv._OekoEnv__inner_step = patched_inner_step

def get_heuristic_action(env):
    V = env.unwrapped.V
    ap = int(V[9])
    dist = np.zeros(5, dtype=int)
    if V[2] + dist[2] < 29 and ap > 0:
        d = min(ap, 29 - (int(V[2]) + dist[2])); dist[2] += int(d); ap -= int(d)
    p_target = 13
    p_dist = p_target - (int(V[1]) + dist[1])
    if ap > 0 and p_dist != 0:
        d = min(max(1, ap // 2), abs(p_dist))
        change = -int(d) if p_dist < 0 else int(d)
        dist[1] += change; ap -= abs(change)
    while ap + int(V[9]) > 28:
        changed = False
        if int(V[2]) + dist[2] < 29: dist[2] += 1; ap -= 1; changed = True
        elif int(V[3]) + dist[3] < 18: dist[3] += 1; ap -= 1; changed = True
        elif int(V[4]) + dist[4] < 15: dist[4] += 1; ap -= 1; changed = True
        elif V[5] < 12:
            if int(V[1]) + dist[1] < 18: dist[1] += 1; ap -= 1; changed = True
            else: break
        elif V[5] > 20:
            if int(V[0]) + dist[0] < 25: dist[0] += 1; ap -= 1; changed = True
        else:
            if int(V[1]) + dist[1] > 5: dist[1] -= 1; ap -= 1; changed = True
            else: break
        if not changed or ap + int(V[9]) <= 28: break
    act = np.zeros(6, dtype=np.int64)
    act[:5] = dist
    if V[6] > 32: act[5] = -4
    elif V[6] < 18: act[5] = 5
    else: act[5] = 0
    return act - env.unwrapped.Amin

def run_heuristic(seed: int) -> dict:
    random.seed(seed)
    np.random.seed(seed)

    env = OekoEnv(render_mode=None)
    env.reset(seed=seed)

    for step_idx in range(60):
        action = get_heuristic_action(env)
        obs, reward, terminated, truncated, info = env.step(action)

        if terminated or truncated:
            break

    final_V = env.unwrapped.V
    inner = env.unwrapped
    rounds_survived = int(final_V[8])
    stability = 30 - (np.max(final_V[:8]) - np.min(final_V[:8]))
    balance = float(getattr(inner, 'balance_always', 0.0))

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
        'model': 'Heuristic',
        'seed': seed,
        'rounds_survived': rounds_survived,
        'stability': float(stability),
        'balance': balance,
        'death_cause': death_cause
    }

def main():
    print("--- Running Heuristic Benchmark ---")
    seeds = list(range(30))
    all_results = []

    for seed in seeds:
        res = run_heuristic(seed)
        all_results.append(res)
        print(f"Seed {seed:02d}: Rounds={res['rounds_survived']:02d}, Balance={res['balance']:.2f}, Stability={res['stability']:.1f}, Death={res['death_cause']}")

    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "heuristic_raw_0_29.csv")
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['model', 'seed', 'rounds_survived', 'stability', 'balance', 'death_cause'])
        writer.writeheader()
        writer.writerows(all_results)

    print(f"Saved heuristic raw data to {csv_path}")

    # Generate the 3-way excel
    logs_dir = os.path.join(ROOT_DIR, "evo10", "logs")
    paper_sovereign_results = []

    for filename in os.listdir(logs_dir):
        if filename.startswith("multiseed_raw_") and filename.endswith(".csv"):
            df = pd.read_csv(os.path.join(logs_dir, filename))
            paper_sovereign_results.append(df)

    if paper_sovereign_results:
        ps_df = pd.concat(paper_sovereign_results, ignore_index=True)
    else:
        ps_df = pd.DataFrame()

    h_df = pd.DataFrame(all_results)

    if not ps_df.empty:
        df_all = pd.concat([ps_df, h_df], ignore_index=True)
    else:
        df_all = h_df

    summary_data = []
    for mode in ["Paper", "Sovereign", "Heuristic"]:
        mode_df = df_all[df_all['model'] == mode]
        n = len(mode_df)
        if n == 0:
            continue

        mean_rounds = mode_df['rounds_survived'].mean()
        std_rounds = mode_df['rounds_survived'].std()
        ci95 = 1.96 * std_rounds / math.sqrt(n) if n > 0 else 0
        survival_rate = (len(mode_df[mode_df['rounds_survived'] >= 30]) / n) * 100

        death_causes = mode_df[mode_df['death_cause'] != 'survived']['death_cause'].tolist()
        if death_causes:
            from collections import Counter
            dominant_death = Counter(death_causes).most_common(1)[0][0]
        else:
            dominant_death = "None"

        summary_data.append({
            'Model': mode,
            'n': n,
            'Mean Rounds ± CI 95%': f"{mean_rounds:.2f} ± {ci95:.2f}",
            'Survival Rate': f"{survival_rate:.1f}%",
            'Dominant Death': dominant_death
        })

    summary_df = pd.DataFrame(summary_data)

    excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evo10_threeway.xlsx")
    with pd.ExcelWriter(excel_path) as writer:
        summary_df.to_excel(writer, sheet_name='summary', index=False)
        df_all.to_excel(writer, sheet_name='raw_data', index=False)

    print(f"Generated Excel report at {excel_path}")

if __name__ == "__main__":
    main()

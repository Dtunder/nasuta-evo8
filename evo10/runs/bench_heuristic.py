import sys
import os
import pandas as pd

# Add src to sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_ROOT = os.path.join(ROOT_DIR, "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

from xai_multiseed import run_heuristic
from sb3_contrib import RecurrentPPO

def main():
    model_path = os.path.join(ROOT_DIR, "brain", "sota_recurrent_champion.zip")
    if os.path.exists(model_path):
        model = RecurrentPPO.load(model_path)
    else:
        model = None

    results = []
    for seed in range(10):
        res = run_heuristic(model, seed)
        res['seed'] = seed
        results.append(res)
        print(f"Seed {seed}: {res}")

    df = pd.DataFrame(results)

    # Reorder columns as requested: {seed, rounds_survived, stability, death_cause}
    df = df[['seed', 'rounds_survived', 'stability', 'death_cause']]

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bench_heuristic.xlsx")
    df.to_excel(out_path, index=False)
    print(f"Saved to {out_path}")

if __name__ == "__main__":
    main()

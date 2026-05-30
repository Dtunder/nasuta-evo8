import sys
import os
import pandas as pd
from sb3_contrib import RecurrentPPO

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT_DIR, "src"))

from xai_multiseed import run_heuristic

def main():
    model_path = os.path.join(ROOT_DIR, "brain", "sota_recurrent_champion.zip")
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        sys.exit(1)

    model = RecurrentPPO.load(model_path)

    results = []
    for seed in range(10):
        res = run_heuristic(model, seed)
        res['seed'] = seed
        results.append(res)

    df = pd.DataFrame(results)
    cols = ['seed', 'rounds_survived', 'stability', 'death_cause']
    df = df[cols]

    out_path = os.path.join(ROOT_DIR, "evo10", "runs", "bench_heuristic.xlsx")
    df.to_excel(out_path, index=False)

if __name__ == "__main__":
    main()

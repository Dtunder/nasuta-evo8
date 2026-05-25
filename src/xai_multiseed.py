import os
import sys
import numpy as np
import torch
import random
import csv
import math
import time
import logging

# Silence MCTS logging to speed up execution and reduce output volume
logging.getLogger("MCTS").setLevel(logging.WARNING)

# Add paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NASUTA_ROOT = os.path.join(ROOT_DIR, "engine")
SRC_ROOT = os.path.join(ROOT_DIR, "src")

for p in [NASUTA_ROOT, SRC_ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Neural Fix
import torch.nn as nn
original_lstm_init = nn.LSTM.__init__
def patched_lstm_init(self, input_size, hidden_size, *args, **kwargs):
    return original_lstm_init(self, int(input_size), int(hidden_size), *args, **kwargs)
nn.LSTM.__init__ = patched_lstm_init

from oeko_core.envs.oeko_env import OekoEnv
from wrappers import OekoActionBuilderWrapper
from sb3_contrib import RecurrentPPO
from mcts_planner import SovereignMCTS
from gymcts.gymcts_deepcopy_wrapper import DeepCopyMCTSGymEnvWrapper
from gymcts.gymcts_action_history_wrapper import ActionHistoryMCTSGymEnvWrapper

def _lstm_zero_states(model):
    """Returns fresh zero LSTM states sized from the model's actual architecture."""
    lstm = getattr(model.policy, 'lstm_actor', None) or getattr(model.policy, 'lstm_critic', None)
    h = getattr(lstm, 'hidden_size', 256)
    layers = getattr(lstm, 'num_layers', 2)
    return (torch.zeros(layers, 1, h), torch.zeros(layers, 1, h))

def action_mask_fn(curr_env):
    curr = curr_env
    while hasattr(curr, 'env'):
        if hasattr(curr, 'valid_action_mask'):
            return curr.valid_action_mask()
        curr = curr.env
    return np.ones(10, dtype=bool)

def run_once(model, sovereign_mode: bool, seed: int) -> dict:
    # Deterministisches Seeding
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
    
    # Environment Pipeline
    base_env = OekoEnv(render_mode=None)
    wrapped_env = OekoActionBuilderWrapper(base_env)
    env = DeepCopyMCTSGymEnvWrapper(wrapped_env)
    env = ActionHistoryMCTSGymEnvWrapper(env, action_mask_fn=action_mask_fn)
    env.reset(seed=seed)

    def is_terminal_bridge(): return env.unwrapped.done
    def get_valid_actions_bridge():
        mask = action_mask_fn(env)
        valid_ids = [idx for idx, m in enumerate(mask) if m]
        return valid_ids if valid_ids else [0]

    env.is_terminal = is_terminal_bridge
    env.get_valid_actions = get_valid_actions_bridge

    # MCTS Planner
    mcts = SovereignMCTS(model, num_simulations=100, render_tree=False, sovereign_mode=sovereign_mode)

    # Simulation Loop
    for step_idx in range(500): # High limit, usually ends at 30
        valid_actions = get_valid_actions_bridge()
        if not valid_actions:
            break
        
        action = mcts.search(env)
        obs, reward, terminated, truncated, info = env.step(action)
        
        if terminated or truncated:
            break

    final_V = env.unwrapped.V
    rounds_survived = int(final_V[8])
    # Stability metric: 30 - (max(V[:8]) - min(V[:8]))
    stability = 30 - (np.max(final_V[:8]) - np.min(final_V[:8]))
    
    # Death cause derivation
    death_cause = 'survived_30'
    if rounds_survived < 30:
        if final_V[7] < -10: death_cause = 'politics_collapse'
        elif final_V[5] > 29: death_cause = 'env_collapse'
        elif final_V[6] > 60: death_cause = 'overpopulation'
        elif final_V[6] < 13: death_cause = 'extinction'
        elif final_V[9] < 1: death_cause = 'no_ap'
        else: death_cause = 'other'
    
    return {
        'rounds_survived': rounds_survived,
        'stability': float(stability),
        'death_cause': death_cause
    }

def main():
    start_seed = int(os.environ.get('START_SEED', '0'))
    end_seed = int(os.environ.get('END_SEED', '20'))
    seeds = list(range(start_seed, end_seed))
    
    model_path = os.path.join(ROOT_DIR, "brain", "sota_recurrent_champion.zip")
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        sys.exit(1)
        
    print(f"Loading model: {model_path}")
    model = RecurrentPPO.load(model_path)
    
    all_results = []
    
    for mode_label, sovereign_mode in [("Paper", False), ("Sovereign", True)]:
        print(f"\n--- Benchmark Mode: {mode_label} (sovereign_mode={sovereign_mode}) ---")
        sys.stdout.flush()
        for seed in seeds:
            start_t = time.time()
            try:
                res = run_once(model, sovereign_mode, seed)
                res['model'] = mode_label
                res['seed'] = seed
                all_results.append(res)
                duration = time.time() - start_t
                print(f"Seed {seed:02d}: Rounds={res['rounds_survived']:02d}, Stability={res['stability']:.1f}, Death={res['death_cause']} ({duration:.1f}s)")
                sys.stdout.flush()
            except Exception as e:
                print(f"Seed {seed:02d} FAILED: {str(e)}")
                sys.stdout.flush()
    
    # Write Raw Data
    log_dir = os.path.join(ROOT_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    raw_csv = os.path.join(log_dir, f"multiseed_raw_{start_seed}_{end_seed}.csv")
    with open(raw_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['model', 'seed', 'rounds_survived', 'stability', 'death_cause'])
        writer.writeheader()
        writer.writerows(all_results)
    
    # Aggregation & Report
    summary_md = os.path.join(log_dir, "multiseed_summary.md")
    report = ["# Oekolopoly Sovereign Death Benchmark - Multi-Seed Summary\n"]
    report.append(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
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
        
    print(f"\nBenchmark finished. Raw data: {raw_csv}, Summary: {summary_md}")
    sys.stdout.flush()

if __name__ == "__main__":
    main()

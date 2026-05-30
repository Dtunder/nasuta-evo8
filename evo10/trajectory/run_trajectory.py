import os
import sys
import numpy as np
import torch
import random
import pandas as pd
import logging

logging.getLogger('MCTS').setLevel(logging.WARNING)

# Add paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NASUTA_ROOT = os.path.join(ROOT_DIR, "engine")
SRC_ROOT = os.path.join(ROOT_DIR, "src")

for p in [NASUTA_ROOT, SRC_ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

from oeko_core.envs.oeko_env import OekoEnv
from wrappers import OekoActionBuilderWrapper
from sb3_contrib import RecurrentPPO
from mcts_planner import SovereignMCTS
from gymcts.gymcts_deepcopy_wrapper import DeepCopyMCTSGymEnvWrapper
from gymcts.gymcts_action_history_wrapper import ActionHistoryMCTSGymEnvWrapper

def action_mask_fn(curr_env):
    curr = curr_env
    while hasattr(curr, 'env'):
        if hasattr(curr, 'valid_action_mask'):
            return curr.valid_action_mask()
        curr = curr.env
    return np.ones(9, dtype=bool)

def run_trajectory(model, sovereign_mode: bool, seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)

    base_env = OekoEnv(render_mode=None)
    wrapped = OekoActionBuilderWrapper(base_env)
    env = DeepCopyMCTSGymEnvWrapper(wrapped)
    env = ActionHistoryMCTSGymEnvWrapper(env, action_mask_fn=action_mask_fn)
    env.reset(seed=seed)

    def is_terminal_bridge(): return env.unwrapped.done
    def get_valid_actions_bridge():
        mask = action_mask_fn(env)
        valid_ids = [idx for idx, m in enumerate(mask) if m]
        return valid_ids if valid_ids else [0]

    env.is_terminal = is_terminal_bridge
    env.get_valid_actions = get_valid_actions_bridge

    mcts = SovereignMCTS(model, num_simulations=50, render_tree=False, sovereign_mode=sovereign_mode)
    steps = []

    for step_idx in range(500):
        action = mcts.search(env)
        obs, r, term, trunc, info = env.step(action)
        V = env.unwrapped.V.copy()
        steps.append({
            "step": step_idx,
            "action": action,
            "V0": V[0], "V1": V[1], "V2": V[2], "V3": V[3], "V4": V[4],
            "V5": V[5], "V6": V[6], "V7": V[7], "V8": V[8], "V9": V[9],
            "done": int(term or trunc)
        })
        if term or trunc: break

    return steps

def main():
    model_path = os.path.join(ROOT_DIR, "brain", "sota_recurrent_champion.zip")
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        sys.exit(1)

    model = RecurrentPPO.load(model_path)

    runs = [(False, 0), (False, 1), (True, 0), (True, 1)]
    all_data = {}
    overview_data = []

    for sovereign_mode, seed in runs:
        label = "Paper" if not sovereign_mode else "Sovereign"
        sheet_name = f"{label}_s{seed}"
        print(f"Running {sheet_name}...")
        steps = run_trajectory(model, sovereign_mode, seed)
        all_data[sheet_name] = pd.DataFrame(steps)
        overview_data.append({
            "mode": label,
            "seed": seed,
            "total_steps": len(steps),
            "rounds_survived": int(steps[-1]["V8"]) if steps else 0
        })

    out_file = os.path.join(ROOT_DIR, "evo10", "trajectory", "evo10_trajectories.xlsx")

    with pd.ExcelWriter(out_file, engine='openpyxl') as writer:
        pd.DataFrame(overview_data).to_excel(writer, sheet_name="Overview", index=False)
        for sheet_name, df in all_data.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    # Bold headers
    import openpyxl
    from openpyxl.styles import Font
    wb = openpyxl.load_workbook(out_file)
    for sheet in wb.worksheets:
        for cell in sheet[1]:
            cell.font = Font(bold=True)
    wb.save(out_file)
    print(f"Saved {out_file}")

if __name__ == "__main__":
    main()

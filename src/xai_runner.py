import os
import sys
import numpy as np
import torch
import time

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
from xai_logger import SovereignXAILogger
from gymcts.gymcts_deepcopy_wrapper import DeepCopyMCTSGymEnvWrapper
from gymcts.gymcts_action_history_wrapper import ActionHistoryMCTSGymEnvWrapper
from gymnasium.wrappers import RecordEpisodeStatistics

def action_mask_fn(curr_env):
    curr = curr_env
    while hasattr(curr, 'env'):
        if hasattr(curr, 'valid_action_mask'):
            return curr.valid_action_mask()
        curr = curr.env
    return np.ones(10, dtype=bool)

def run_paper_failure(model, logger):
    print("--- Running Run 1: The Paper's Failure (Pure MCTS) ---")
    base_env = OekoEnv(render_mode="ansi")
    wrapped_env = OekoActionBuilderWrapper(base_env)
    env = DeepCopyMCTSGymEnvWrapper(wrapped_env)
    env = ActionHistoryMCTSGymEnvWrapper(env, action_mask_fn=action_mask_fn)
    env.reset()

    def is_terminal_bridge(): return env.unwrapped.done
    def get_valid_actions_bridge():
        mask = action_mask_fn(env)
        valid_ids = [idx for idx, m in enumerate(mask) if m]
        return valid_ids if valid_ids else [0]

    env.is_terminal = is_terminal_bridge
    env.get_valid_actions = get_valid_actions_bridge

    def safe_stats_step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        return obs, reward, terminated, truncated, info
    RecordEpisodeStatistics.step = safe_stats_step

    mcts = SovereignMCTS(model, num_simulations=100, render_tree=False)

    logs = []
    burn_events = 0

    for step_idx in range(500):
        V_before = env.unwrapped.V.copy()

        valid_actions = get_valid_actions_bridge()
        if not valid_actions:
            break

        action = mcts.search(env)

        obs = env.unwrapped.obs
        obs_fixed = np.array([obs], dtype=np.float32)
        lstm_states = (torch.zeros(2, 1, 256), torch.zeros(2, 1, 256))
        episode_starts = torch.ones(1, dtype=torch.float32)
        val = model.policy.predict_values(torch.as_tensor(obs_fixed), lstm_states, episode_starts).detach()
        value_est = float(val[0][0])

        obs, reward, terminated, truncated, info = env.step(action)

        V_after = env.unwrapped.V.copy()

        if action == 0:
            log_line = logger.explain_action(V_before, V_after, action, value_est)
            logs.append(log_line)
            if "BURN" in log_line:
                burn_events += 1

        if terminated or truncated:
            break

    rounds_survived = int(env.unwrapped.V[8])
    final_score = int(env.unwrapped.V[9])
    balance = info.get('balance', 0) if 'info' in locals() else 0
    summary = f"Rounds survived: {rounds_survived} | Final score: {balance} | Burn events: {burn_events}"
    logs.append(summary)

    log_dir = os.path.join(ROOT_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, "xai_paper_death_log.txt"), "w") as f:
        f.write("\n".join(logs) + "\n")
    print(summary)


def run_sovereign_success(model, logger):
    print("--- Running Run 2: The Sovereign Success (Hybrid Heuristic) ---")
    base_env = OekoEnv(render_mode="ansi")
    env = OekoActionBuilderWrapper(base_env)
    env.reset()

    logs = []
    burn_events = 0

    # Run loop 30 times directly simulating the heuristic fallback
    for _ in range(30):
        V_before = env.unwrapped.V.copy()
        ap = int(V_before[9])

        # Calculate Value estimate
        obs = env.unwrapped.obs
        obs_fixed = np.array([obs], dtype=np.float32)
        lstm_states = (torch.zeros(2, 1, 256), torch.zeros(2, 1, 256))
        episode_starts = torch.ones(1, dtype=torch.float32)
        val = model.policy.predict_values(torch.as_tensor(obs_fixed), lstm_states, episode_starts).detach()
        value_est = float(val[0][0])

        dist = np.zeros(5, dtype=int)
        V = V_before

        # The heuristic fallback logic
        if V[2] + dist[2] < 29 and ap > 0:
            d = min(ap, 29 - (int(V[2]) + dist[2])); dist[2] += int(d); ap -= int(d)
        p_target = 13
        p_dist = p_target - (int(V[1]) + dist[1])
        if ap > 0 and p_dist != 0:
            d = min(max(1, ap // 2), abs(p_dist))
            change = -int(d) if p_dist < 0 else int(d)
            dist[1] += change; ap -= abs(change)
        while ap + int(V_before[9]) > 28:
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
            if not changed or ap + int(V_before[9]) <= 28: break

        act = np.zeros(6, dtype=np.int64)
        act[:5] = dist
        if V[6] > 32: act[5] = -4
        elif V[6] < 18: act[5] = 5
        else: act[5] = 0
        a = act - env.unwrapped.Amin

        obs, reward, terminated, truncated, info = env.unwrapped.step(a)

        V_after = env.unwrapped.V.copy()
        log_line = logger.explain_action(V_before, V_after, 0, value_est)
        logs.append(log_line)
        if "BURN" in log_line:
            burn_events += 1

        if terminated or truncated:
            break

    rounds_survived = int(env.unwrapped.V[8])
    final_score = int(env.unwrapped.V[9])
    balance = info.get('balance', 0) if 'info' in locals() else 0
    summary = f"Rounds survived: {rounds_survived} | Final score: {balance} | Burn events: {burn_events}"
    logs.append(summary)

    log_dir = os.path.join(ROOT_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, "xai_sovereign_survival_log.txt"), "w") as f:
        f.write("\n".join(logs) + "\n")
    print(summary)


def main():
    model_path = os.path.join(ROOT_DIR, "brain", "sota_recurrent_champion.zip")
    model = RecurrentPPO.load(model_path)
    logger = SovereignXAILogger()

    run_paper_failure(model, logger)
    run_sovereign_success(model, logger)

if __name__ == "__main__":
    main()

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

    # Pure MCTS (Using default MCTS without Sovereign restrictions)
    mcts = SovereignMCTS(model, num_simulations=100, render_tree=False, sovereign_mode=False)

    logs = []
    
    for step_idx in range(500):
        V_before = env.unwrapped.V.copy()

        valid_actions = get_valid_actions_bridge()
        if not valid_actions:
            break

        action = mcts.search(env)

        obs = env.unwrapped.obs
        obs_fixed = np.array([obs], dtype=np.float32)
        lstm_states = _lstm_zero_states(model)
        episode_starts = torch.ones(1, dtype=torch.float32)
        val = model.policy.predict_values(torch.as_tensor(obs_fixed), lstm_states, episode_starts).detach()
        value_est = float(val[0][0])

        obs, reward, terminated, truncated, info = env.step(action)

        V_after = env.unwrapped.V.copy()

        if action == 0:
            log_line = logger.explain_action(V_before, V_after, action, value_est)
            logs.append(log_line)

        if terminated or truncated:
            break

    rounds_survived = int(env.unwrapped.V[8])
    stability = 30 - (np.max(env.unwrapped.V[:8]) - np.min(env.unwrapped.V[:8]))
    summary = f"Rounds survived: {rounds_survived} | Final Stability: {stability:.1f}"
    logs.append(summary)

    log_dir = os.path.join(ROOT_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, "xai_paper_death_log.txt"), "w") as f:
        f.write("\n".join(logs) + "\n")
    print(summary)


def run_sovereign_mcts_equilibrium(model, logger):
    print("--- Running Run 2: Sovereign MCTS Equilibrium (Evo 8) ---")
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

    mcts = SovereignMCTS(model, num_simulations=100, render_tree=False)

    logs = []

    for step_idx in range(500):
        V_before = env.unwrapped.V.copy()

        valid_actions = get_valid_actions_bridge()
        if not valid_actions:
            break

        action = mcts.search(env)

        # Calculate Value estimate
        obs = env.unwrapped.obs
        obs_fixed = np.array([obs], dtype=np.float32)
        lstm_states = _lstm_zero_states(model)
        episode_starts = torch.ones(1, dtype=torch.float32)
        val = model.policy.predict_values(torch.as_tensor(obs_fixed), lstm_states, episode_starts).detach()
        value_est = float(val[0][0])

        obs, reward, terminated, truncated, info = env.step(action)

        V_after = env.unwrapped.V.copy()
        
        if action == 0:
            log_line = logger.explain_action(V_before, V_after, action, value_est)
            logs.append(log_line)

        if terminated or truncated:
            break

    rounds_survived = int(env.unwrapped.V[8])
    stability = 30 - (np.max(env.unwrapped.V[:8]) - np.min(env.unwrapped.V[:8]))
    summary = f"Rounds survived: {rounds_survived} | Final Stability: {stability:.1f}"
    logs.append(summary)

    log_dir = os.path.join(ROOT_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, "xai_sovereign_equilibrium_log.txt"), "w") as f:
        f.write("\n".join(logs) + "\n")
    print(summary)


def main():
    model_path = os.path.join(ROOT_DIR, "brain", "sota_recurrent_champion.zip")
    model = RecurrentPPO.load(model_path)
    logger = SovereignXAILogger()

    run_paper_failure(model, logger)
    run_sovereign_mcts_equilibrium(model, logger)

if __name__ == "__main__":
    main()

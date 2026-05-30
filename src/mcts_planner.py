import os
import sys
import numpy as np
import gymnasium as gym
import torch.nn as nn

# MANDATORY SOVEREIGN LSTM PATCH (Fixes PyTorch/Gymnasium int64 conflict)
original_lstm_init = nn.LSTM.__init__
def patched_lstm_init(self, input_size, hidden_size, *args, **kwargs):
    return original_lstm_init(self, int(input_size), int(hidden_size), *args, **kwargs)
nn.LSTM.__init__ = patched_lstm_init

# NESTED WRAPPER COLLISION FIX (Fixes RecordEpisodeStatistics AssertionError on duplicate "episode" key)
from gymnasium.wrappers import RecordEpisodeStatistics
import time

_orig_statistics_step = RecordEpisodeStatistics.step
def _patched_statistics_step(self, action):
    obs, reward, terminated, truncated, info = self.env.step(action)
    self.episode_returns += reward
    self.episode_lengths += 1
    if terminated or truncated:
        if self._stats_key in info:
            info.pop(self._stats_key, None)  # Prevent AssertionError collision
        episode_time_length = round(time.perf_counter() - self.episode_start_time, 6)
        info[self._stats_key] = {
            "r": self.episode_returns,
            "l": self.episode_lengths,
            "t": episode_time_length,
        }
        self.time_queue.append(episode_time_length)
        self.return_queue.append(self.episode_returns)
        self.length_queue.append(self.episode_lengths)
        self.episode_count += 1
        self.episode_start_time = time.perf_counter()
    return obs, reward, terminated, truncated, info
RecordEpisodeStatistics.step = _patched_statistics_step


# Priority paths for Nasuta's original work
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NASUTA_ROOT = os.path.join(ROOT_DIR, "reference_nasuta_gymcts", "gymcts-games-main", "src")
if NASUTA_ROOT not in sys.path:
    sys.path.insert(0, NASUTA_ROOT)

# Register env if not already registered (allows standalone use of mcts_planner)
from gymnasium.envs.registration import register as _gym_register
try:
    _gym_register(id='oeko_core-v2', entry_point='oeko_core.envs.oeko_env:OekoEnv')
except Exception:
    pass  # Already registered

# GLOBAL SOVEREIGN COMPONENTS (Avoids DeepCopy overhead)
_GLOBAL_SOVEREIGN_MODEL = None
_GLOBAL_SOVEREIGN_MODE = False  # Bug C fix: passed to class-level patch without closure


def _sovereign_get_valid_actions(self):
    """Class-level patch for get_valid_actions — each deepcopy reads its OWN state (Bug C fix).

    Replaces the closure-based instance attribute that previously caused all MCTS tree nodes
    to read action masks from the original env instead of their own deepcopied state.
    Uses _get_mask_from_chain() because gym.Wrapper has no __getattr__ proxy here.
    """
    # Bug A fix pattern: traverse __dict__ to bypass gym.Wrapper.__getattr__ blocking _ attrs
    curr = self
    avail = self.env.unwrapped.V[9]
    while curr is not None:
        if '_available_action_points' in getattr(curr, '__dict__', {}):
            avail = int(curr.__dict__['_available_action_points'])
            break
        curr = getattr(curr, 'env', None)

    valid = [i for i, v in enumerate(_get_mask_from_chain(self)) if v]

    if _GLOBAL_SOVEREIGN_MODE:
        V = self.env.unwrapped.V

        # Helper: read _current_action_dict from own __dict__ chain
        def _own_action_dict():
            c = self
            while c is not None:
                if '_current_action_dict' in getattr(c, '__dict__', {}):
                    return c.__dict__['_current_action_dict']
                c = getattr(c, 'env', None)
            return {}

        if avail > 0:
            if V[3] < 8:
                if 5 in valid:
                    return [5]
            elif V[3] < 12:
                last = _own_action_dict()
                if last.get("Production", 0) > last.get("Quality of Life", 0):
                    if 5 in valid:
                        return [5]

        if avail > 0 and 2 in valid:
            prod_invested = _own_action_dict().get("Production", 0)
            if prod_invested >= max(2, V[9] // 2.5):
                valid.remove(2)

    if avail > 0 and 0 in valid and len(valid) > 1:
        valid.remove(0)
    return valid

def _get_mask_from_chain(wrapper):
    """Traverse the wrapper chain to find valid_action_mask on OekoActionBuilderWrapper.

    gym.Wrapper has no __getattr__ in this Gymnasium version, so attributes on inner
    wrappers are NOT automatically proxied. We must traverse manually.
    """
    curr = wrapper
    while curr is not None:
        if 'valid_action_mask' in type(curr).__dict__:
            return curr.valid_action_mask()
        curr = getattr(curr, 'env', None)
    return [True] * 9  # fallback: all actions valid


def guided_rollout_wrapper(self_wrapper):
    """Uses a FAST heuristic for massive simulation throughput."""
    try:
        temp_env = self_wrapper.env.unwrapped
        total_reward = 0
        d_done = False
        rounds_played = 0  # FIX: count ROUNDS not individual AP allocations

        while not d_done and rounds_played < 50:  # safety cap for rollout simulations
            V = temp_env.V
            # Bug A fix: gym.Wrapper.__getattr__ blocks _-prefixed attrs, so traverse __dict__
            curr = self_wrapper
            avail = int(V[9])
            while curr is not None:
                if '_available_action_points' in getattr(curr, '__dict__', {}):
                    avail = int(curr.__dict__['_available_action_points'])
                    break
                curr = getattr(curr, 'env', None)

            if temp_env.done:
                break

            # Bug B fix: gym.Wrapper has no __getattr__ proxy in this Gymnasium version,
            # so traverse chain manually to reach OekoActionBuilderWrapper.valid_action_mask()
            valid_actions = [i for i, v in enumerate(_get_mask_from_chain(self_wrapper)) if v]
            if not valid_actions:
                break

            # HEURISTIC SELECTION (Survival-First Sovereign Logic)
            if avail > 0:
                # 1. CRITICAL PROTECTION: Quality of Life (Protects Politics/Stability)
                if 5 in valid_actions and V[3] < 15: move = 5
                # 2. SYSTEMIC STABILITY: Production (build it up if low) — FIX: was V[7] (Politics), must be V[1]
                elif 2 in valid_actions and V[1] < 10: move = 2
                # 3. ENVIRONMENTAL RECOVERY: Sanitation
                elif 1 in valid_actions and V[5] < 15: move = 1
                # 4. EDUCATION (Long-term)
                elif 4 in valid_actions and V[2] < 15: move = 4
                else:
                    # If stable, diversify
                    investments = [a for a in valid_actions if a != 0]
                    move = np.random.choice(investments) if investments else 0
            else:
                move = 0 # Must end round

            obs_ext, rew, term, trunc, info = self_wrapper.step(move)

            # FIX: Compute stability on V AFTER the step, not before
            V_after = temp_env.V
            stability = 30 - (np.max(V_after[:8]) - np.min(V_after[:8]))
            total_reward += stability + rew
            if move == 0:
                total_reward += 10000
                rounds_played += 1  # FIX: only increment round counter when round ends

            d_done = term or trunc

        return total_reward
    except Exception as e:
        return -5000000

class SovereignMCTS:
    def __init__(self, model, num_simulations=1000, render_tree=True, sovereign_mode=True):
        """
        Initializes the Sovereign MCTS Planner.
        
        Args:
            model: The RecurrentPPO model to use as a policy guide.
            num_simulations: How many 'futures' to simulate (Default 3000 for Nasuta-style deep thinking).
            render_tree: Whether to print the visual MCTS tree to console.
            sovereign_mode: Whether to enable Humanity Limit and Industrial Cap restrictions.
        """
        self.model = model
        self.num_simulations = num_simulations
        self.render_tree = render_tree
        self.sovereign_mode = sovereign_mode

    def search(self, env) -> int:
        """
        Performs a deep MCTS search guided by the neural policy.
        """
        global _GLOBAL_SOVEREIGN_MODEL, _GLOBAL_SOVEREIGN_MODE
        _GLOBAL_SOVEREIGN_MODEL = self.model
        _GLOBAL_SOVEREIGN_MODE = self.sovereign_mode

        # Create a simulation copy
        sim_env = gym.make("oeko_core-v2")

        # Import Nasuta's specialized MCTS components
        from gymcts.gymcts_agent import GymctsAgent
        from gymcts.gymcts_deepcopy_wrapper import DeepCopyMCTSGymEnvWrapper
        from wrappers import OekoActionBuilderWrapper

        # 1. Wrap with ActionBuilder (Nasuta's translation layer)
        wrapped_env = OekoActionBuilderWrapper(sim_env)

        # 2. Wrap with DeepCopy (State management for MCTS)
        wrapped_env = DeepCopyMCTSGymEnvWrapper(wrapped_env)

        # Save originals — both rollout and get_valid_actions are patched at class level
        # so every deepcopy node uses its own state (Bug B fix = rollout, Bug C fix = get_valid_actions)
        _orig_rollout = DeepCopyMCTSGymEnvWrapper.rollout
        _orig_get_valid_actions = DeepCopyMCTSGymEnvWrapper.get_valid_actions

        wrapped_env.reset()
        
        # 5. FULL STATE SYNC (Wrapper-Aware)
        unwrapped_real = env.unwrapped
        unwrapped_sim = wrapped_env.env.unwrapped
        
        # Sync Base Environment
        unwrapped_sim.V = unwrapped_real.V.copy()
        unwrapped_sim.obs = unwrapped_real.obs.copy()
        unwrapped_sim.done = unwrapped_real.done
        
        # Sync ActionBuilder Wrapper State (Robust layer search)
        def sync_wrapper(src, dst):
            s_curr = src
            while s_curr is not None:
                if hasattr(s_curr, '_current_action_dict'):
                    d_curr = dst
                    while d_curr is not None:
                        if hasattr(d_curr, '_current_action_dict'):
                            # SYNC FOUND — copy all wrapper state including direction flags
                            d_curr._available_action_points = int(s_curr._available_action_points)
                            d_curr._available_extra_points = int(s_curr._available_extra_points)
                            for key in s_curr._current_action_dict:
                                d_curr._current_action_dict[key] = s_curr._current_action_dict[key]
                            # FIX: sync direction flags so MCTS sees the same action constraints
                            d_curr._production_change_direction = s_curr._production_change_direction
                            d_curr._population_extra_change_direction = s_curr._population_extra_change_direction
                            return True
                        d_curr = getattr(d_curr, 'env', None)
                s_curr = getattr(s_curr, 'env', None)
            return False

        sync_wrapper(env, wrapped_env)
        
        # Setup MCTS Agent with Nasuta's original parameters
        agent = GymctsAgent(
            env=wrapped_env, 
            number_of_simulations_per_step=self.num_simulations,
            render_tree_after_step=self.render_tree,
            render_tree_max_depth=2 
        )
        
        # Perform the actual deep search
        import sys
        import logging
        m_logger = logging.getLogger("MCTS")
        m_logger.info("\n" + "="*50)
        m_logger.info(" [SOVEREIGN DEEP THINKING TREE START]")
        sys.stdout.flush()
        
        try:
            DeepCopyMCTSGymEnvWrapper.rollout = guided_rollout_wrapper
            DeepCopyMCTSGymEnvWrapper.get_valid_actions = _sovereign_get_valid_actions
            try:
                action = agent.vanilla_mcts_search(num_simulations=self.num_simulations)
            except Exception as e:
                if "charmap" in str(e):
                    m_logger.warning(" [Encoding Error] Tree contains characters not supported by console. Falling back to simple best move.")
                    action = agent.search_root_node.get_best_action()
                else:
                    raise e
        finally:
            DeepCopyMCTSGymEnvWrapper.rollout = _orig_rollout
            DeepCopyMCTSGymEnvWrapper.get_valid_actions = _orig_get_valid_actions
        
        m_logger.info(" [SOVEREIGN DEEP THINKING TREE END]")
        m_logger.info("="*50)
        m_logger.info(f"\n [Sovereign Analysis] Search complete. Best Move: {action}")
        sys.stdout.flush()
        
        return action

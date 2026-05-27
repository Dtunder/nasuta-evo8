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

def guided_rollout_wrapper(self_wrapper):
    """Uses a FAST heuristic for massive simulation throughput."""
    try:
        temp_env = self_wrapper.env.unwrapped
        total_reward = 0
        d_done = False
        rounds_played = 0  # FIX: count ROUNDS not individual AP allocations

        while not d_done and rounds_played < 200:  # safety cap for rollout simulations
            V = temp_env.V
            # SYNC FIX: Access the wrapper's internal AP tracker if available
            if hasattr(self_wrapper, '_available_action_points'):
                avail = int(self_wrapper._available_action_points)
            else:
                avail = int(V[9])

            if temp_env.done:
                break

            valid_actions = self_wrapper.get_valid_actions()
            if not valid_actions: break

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
        global _GLOBAL_SOVEREIGN_MODEL
        _GLOBAL_SOVEREIGN_MODEL = self.model
        
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
        
        # 3. Add MCTS Bridges (Robust recursive search for Nasuta compatibility)
        def find_valid_mask():
            curr = wrapped_env
            while curr is not None:
                if hasattr(curr, 'valid_action_mask'):
                    return curr.valid_action_mask()
                curr = getattr(curr, 'env', None)
            return [True] * 9 # Fallback
            
        def get_sovereign_valid_actions():
            mask = find_valid_mask()
            # SYNC FIX
            if hasattr(wrapped_env, '_available_action_points'):
                avail = int(wrapped_env._available_action_points)
            else:
                avail = int(wrapped_env.env.unwrapped.V[9])
                
            valid = [i for i, v in enumerate(mask) if v]
            
            if self.sovereign_mode:
                # SOVEREIGN GOVERNANCE: Humanity Protocol (Anti-Suicide Layer)
                V_real = wrapped_env.env.unwrapped.V
                
                # 1. THE HUMANITY LIMIT: If QoL is dropping, we MUST invest in QoL (Action 5)
                # If QoL < 12, we force a 1:1 balance with Production or absolute priority if < 8
                if avail > 0:
                    if V_real[3] < 8:
                        if 5 in valid: return [5] # Absolute survival
                    elif V_real[3] < 12:
                        # Forced balance: If we just did Prod, we MUST do QoL
                        last_actions = getattr(wrapped_env, '_current_action_dict', {})
                        if last_actions.get("Production", 0) > last_actions.get("Quality of Life", 0):
                            if 5 in valid: return [5]
                
                # 2. THE INDUSTRIAL CAP: Never spend more than 40% of AP on Production in one turn
                # unless everything else is perfect.
                if avail > 0 and 2 in valid:
                    prod_invested = getattr(wrapped_env, '_current_action_dict', {}).get("Production", 0)
                    total_ap_start = V_real[9]
                    if prod_invested >= max(2, total_ap_start // 2.5):
                        if 2 in valid: valid.remove(2) # Soft cap
            
            # HARD MASKING: Only remove Action 0 if there's SOMETHING ELSE to do
            if avail > 0 and 0 in valid and len(valid) > 1:
                valid.remove(0)
            return valid

        wrapped_env.get_valid_actions = get_sovereign_valid_actions

        # Save original rollout so it can be restored after search
        _orig_rollout = DeepCopyMCTSGymEnvWrapper.rollout

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
        
        m_logger.info(" [SOVEREIGN DEEP THINKING TREE END]")
        m_logger.info("="*50)
        m_logger.info(f"\n [Sovereign Analysis] Search complete. Best Move: {action}")
        sys.stdout.flush()
        
        return action

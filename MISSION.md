# MISSION BRIEFING: Explainable AI (XAI)

@Jules, this is the most critical repository for "Operation Nasuta Evolution". Our supervisor's main critique is that the neural MCTS is a **"Black Box"**. We need to prove *why* the pure Paper methodology dies in round 15.

Your mission is to build an **XAI (Explainable AI) Logger**. You must translate the cold, mathematical delta changes in the `V` state vector and the neural value estimates into **human-readable, narrative text**. We want the AI to justify its own decisions — both when it survives and when it dies.

## TECHNICAL CONTEXT

The codebase is fully functional. Key files:
- `src/oeko_core/envs/oeko_env.py` → class `OekoEnv`
  - State vector `V`: `[QoL, Prod, Edu, Cap, PopG, Env, Pol, San, Round, AP]`
  - Index:            `[  0,    1,   2,   3,   4,   5,   6,   7,     8,  9]`
  - Termination reasons are in `info["done_reason"]` after `step()`
- `src/mcts_planner.py` → MCTS search that selects actions
- `src/wrappers.py` → class `OekoActionBuilderWrapper`

## YOUR EXACT TASK

1. **Create Logger:** Write `src/xai_logger.py` with class `SovereignXAILogger`:
   ```python
   class SovereignXAILogger:
       SECTOR_NAMES = {0:"Quality of Life", 1:"Production", 2:"Education",
                       3:"Capital", 4:"Population Growth", 5:"Environment",
                       6:"Politics", 7:"Sanitation"}
       DANGER_THRESHOLD = 25

       def explain_action(self, V_before, V_after, action_idx, value_estimate) -> str:
           round_num = int(V_before[8])
           ap_before = int(V_before[9])
           changed = [(i, V_before[i], V_after[i])
                      for i in range(8) if V_before[i] != V_after[i]]

           reasons = []
           for sector_idx, old, new in changed:
               name = self.SECTOR_NAMES[sector_idx]
               if sector_idx == 1 and new < old:  # Production decreased
                   reasons.append(f"BURN: Reduced {name} by {int(old-new)} "
                                  f"to prevent AP overflow (AP={ap_before})")
               elif old > self.DANGER_THRESHOLD:
                   reasons.append(f"CRITICAL: {name} was at {int(old)}/29 - "
                                  f"emergency correction applied")
               else:
                   reasons.append(f"Invested +{int(new-old)} in {name} "
                                  f"({int(old)} -> {int(new)})")

           confidence = min(1.0, max(0.0, (value_estimate + 5000) / 10000))
           flags = []
           if ap_before > 25: flags.append("WARNING: High AP risk")
           if any(V_before[i] > 25 or V_before[i] < 5 for i in range(8)):
               flags.append("ALERT: Sector near critical boundary")

           log = f"[Round {round_num:02d}] " + " | ".join(reasons) if reasons else f"[Round {round_num:02d}] No investment this step"
           if flags: log += f"  [{', '.join(flags)}]"
           log += f"  (Neural confidence: {confidence:.2f})"
           return log
   ```

2. **Write `src/xai_runner.py`** that:
   - Plays one full 30-round game using the existing MCTS planner
   - Captures `V_before` and `V_after` around every `env.step()` call
   - Calls `SovereignXAILogger().explain_action(...)` after every step
   - Saves the complete game narrative to `logs/xai_game_log.txt`
   - Prints a summary: `"Rounds survived: X | Final score: Y | Burn events: Z"`

3. **Create** the `logs/` directory if it doesn't exist.

## CONSTRAINTS
- The log must be readable by a non-technical supervisor
- Use clear English sentences, not raw numbers
- Do NOT modify the environment, MCTS, or training logic

## SUCCESS CRITERIA
- `logs/xai_game_log.txt` must contain a human-readable narrative of one complete game
- Each round must have at least one log line explaining the AI's investment decision
- At least one line must contain the word "BURN" (proving Destructive Burn was detected)
- Commit with message: `feat(evo7): SovereignXAILogger for transparent decision narrative`

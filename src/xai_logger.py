import numpy as np

class SovereignXAILogger:
    SECTOR_NAMES = {0:"Sanitation", 1:"Production", 2:"Education",
                    3:"Quality of Life", 4:"Population Growth", 5:"Environment",
                    6:"Population", 7:"Politics"}
    DANGER_THRESHOLD = 25

    def explain_action(self, V_before, V_after, action_idx, value_estimate) -> str:
        round_num = int(V_before[8])
        ap_before = int(V_before[9])
        changed = [(i, V_before[i], V_after[i])
                   for i in range(8) if V_before[i] != V_after[i]]

        reasons = []
        for sector_idx, old, new in changed:
            name = self.SECTOR_NAMES.get(sector_idx, f"Sector {sector_idx}")
            if sector_idx == 1 and new < old:  # Production decreased
                reasons.append(f"BURN: Reduced {name} by {int(old-new)} "
                               f"to prevent AP overflow (AP={ap_before})")
            elif old > self.DANGER_THRESHOLD:
                reasons.append(f"CRITICAL: {name} was at {int(old)}/29 - "
                               f"emergency correction applied")
            else:
                change = int(new-old)
                sign = "+" if change > 0 else ""
                reasons.append(f"Invested {sign}{change} in {name} "
                               f"({int(old)} -> {int(new)})")

        confidence = 1.0 / (1.0 + np.exp(-value_estimate * 0.001))
        stability = 30 - (np.max(V_after[:8]) - np.min(V_after[:8]))
        
        flags = []
        if ap_before > 25: flags.append("WARNING: High AP risk")
        if any(V_before[i] > 25 or V_before[i] < 5 for i in range(8)):
            flags.append("ALERT: Sector near critical boundary")

        log = f"[Round {round_num:02d}] " + " | ".join(reasons) if reasons else f"[Round {round_num:02d}] No investment this step"
        if flags: log += f"  [{', '.join(flags)}]"
        log += f"  (Confidence: {confidence:.2f} | Equilibrium: {stability:.1f})"
        return log

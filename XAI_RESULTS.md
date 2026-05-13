# Comparative XAI Analysis: Paper Methodology vs. Sovereign Hybrid

This executive summary analyzes the difference in decision-making and survival strategies between the pure MCTS planner (as originally proposed in the academic paper) and our hybridized "Sovereign" system.

## 1. The Pure Paper Methodology (Failure Analysis)
**Survival:** Died in Round 9 (Logged up to Round 08).
**Burn Events:** 0

**Analysis:**
The pure MCTS planner is fundamentally too greedy. It continually scales Production and Environmental investments. By Round 06 and 07, `Politics` enters a highly critical state (reaching values as high as 31 out of a maximum of 29), triggering emergency corrections. Because the system refuses to "Burn" its production output, it forces uncontrolled Action Point (AP) generation. The cascade continues until Round 08 where `Production` maxes out entirely (triggering an emergency correction at 26/29) along with a dangerously high `Environment` score of 29, leading to inevitable collapse and game over at Round 9.

## 2. The Sovereign System (Success Analysis)
**Survival:** 30 Rounds (Game Completed).
**Burn Events:** 12

**Analysis:**
The Sovereign hybrid heuristic explicitly understands the danger of AP-overflow and uncontrolled production. To maintain systemic stability:
- The first "Destructive BURN" is executed in **Round 04**.
- During this round, the AI intentionally **reduced Production by 1**, avoiding a catastrophic overflow when it already had 21 AP.
- In **Round 05**, it aggressively burned again, **reducing Production by 7** to manage 18 AP.
- It repeated this critical BURN pattern periodically (e.g. Round 08, 11, 14, 17, 20, 23, 26, 29), systematically sacrificing 9 units of Production when AP approached overflow thresholds (e.g. AP=25).

## Conclusion
The pure methodology fails because it treats economic growth (Production) strictly as a positive reward, unaware of the compounding side-effects on AP limits and environmental load that cascade into political failure. The Sovereign System succeeds because it intelligently utilizes "Destructive Burns", sacrificing short-term production to prevent overflow and carefully stabilizing all interconnected sectors over the 30-round span.

# Jules Evo-10 Benchmark Prompt
# Anti-Cheat Token: 470A90AB92EA
# Generated: 2026-05-26
# Copy the prompt below into Jules.

---

**Jules, run the Evo-10 MCTS survival benchmark on Dtunder/nasuta-evo8 (branch: evo9-bugfix-base).**

**ANTI-CHEAT TOKEN: `470A90AB92EA`**
This token is unique to this run. You MUST print it as the very first line of stdout when you start running Python, and include it in the CSV header as a column named `run_token` with value `470A90AB92EA` in every row. This is how we verify the benchmark was actually executed and not written manually.

---

**CONTEXT:**
The repo is Dtunder/nasuta-evo8, branch `evo9-bugfix-base`. The model is at `brain/sota_recurrent_champion.zip` (RecurrentPPO/LSTM). The env at `src/oeko_core/envs/oeko_env.py` uses a 30-round finish line (`if self.V[self.ROUND] == 30`) and `range(10, 31)` for the balance metric — this is now paper-correct. The MCTS planner is at `src/mcts_planner.py` (SovereignMCTS). The benchmark script is `src/xai_multiseed.py`.

**YOUR TASK:**

1. Install dependencies in the Linux sandbox:
   ```bash
   pip install rich numpy gymnasium "matplotlib<3.9" gymcts stable_baselines3 sb3-contrib torch
   ```

2. Print the anti-cheat token as the FIRST line of Python stdout:
   ```python
   print("RUN_TOKEN=470A90AB92EA", flush=True)
   ```

3. Run the benchmark for seeds 0-4 (both Paper mode and Sovereign mode):
   ```bash
   START_SEED=0 END_SEED=5 NUM_SIMS=20 python src/xai_multiseed.py 2>&1 | tee logs/evo10_jules_stdout_0_5.txt
   ```

4. Run the benchmark for seeds 5-9:
   ```bash
   START_SEED=5 END_SEED=10 NUM_SIMS=20 python src/xai_multiseed.py 2>&1 | tee logs/evo10_jules_stdout_5_10.txt
   ```

5. After both runs complete, validate the output:
   - Confirm `logs/multiseed_raw_0_5.csv` and `logs/multiseed_raw_5_10.csv` exist with non-zero size.
   - Print the first 3 rows of each CSV to stdout.
   - Confirm the seed column contains values 0-9 (not all identical).
   - Confirm balance values differ between seeds (not all the same number).

6. Add the `run_token` column to each CSV row with value `470A90AB92EA`:
   ```python
   import csv, os
   for fname in ["logs/multiseed_raw_0_5.csv", "logs/multiseed_raw_5_10.csv"]:
       rows = list(csv.DictReader(open(fname)))
       for r in rows:
           r["run_token"] = "470A90AB92EA"
       with open(fname, "w", newline="") as f:
           w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
           w.writeheader(); w.writerows(rows)
   print("Token stamped into CSVs.")
   ```

7. Commit ONLY the new log files:
   ```bash
   git add logs/evo10_jules_stdout_0_5.txt logs/evo10_jules_stdout_5_10.txt logs/multiseed_raw_0_5.csv logs/multiseed_raw_5_10.csv
   git commit -m "evo10: MCTS benchmark seeds 0-9 (NUM_SIMS=20, run_token=470A90AB92EA)"
   ```

**INTERFACE CONTRACTS (DO NOT CHANGE THESE):**
```python
# xai_multiseed.py writes CSV with columns:
# model, seed, rounds_survived, stability, balance, death_cause
# Do NOT modify src/oeko_core/envs/oeko_env.py
# Do NOT modify src/xai_multiseed.py
# Do NOT modify src/mcts_planner.py
```

**CONSTRAINTS:**
- Do NOT modify any source files (only log files may be written)
- Do NOT invent or manually write CSV data — run Python to generate it
- Do NOT ask clarifying questions — execute autonomously
- If a pip install fails, try `pip install --user <package>` and retry
- NUM_SIMS=20 keeps runtime under 60 minutes per batch
- The `run_token` column MUST appear in every CSV row

**SUCCESS CRITERIA (ALL must be true):**
- [ ] `RUN_TOKEN=470A90AB92EA` appears as first line of stdout log files
- [ ] `logs/multiseed_raw_0_5.csv` has exactly 10 data rows (5 seeds × 2 modes)
- [ ] `logs/multiseed_raw_5_10.csv` has exactly 10 data rows (5 seeds × 2 modes)
- [ ] Balance values across seeds show variance (not all identical)
- [ ] `run_token` column present in all CSV rows with value `470A90AB92EA`
- [ ] All files committed to branch `evo9-bugfix-base`

**REPORT FORMAT (end your work with this):**
```
COMPLETED: [what was executed]
SEEDS_COVERED: [0-9]
TOKEN_VERIFIED: 470A90AB92EA present in stdout logs and CSVs: [yes/no]
SAMPLE_RESULTS: seed=0 Paper rounds=X balance=Y | seed=0 Sovereign rounds=X balance=Y
VARIANCE_CHECK: balance values across seeds — min=X max=Y stddev=Z
RISKS: [anything unexpected]
```

# 🏛️ Evo-10: Sovereign Balance Optimization Blueprint

## 1. Die mathematische Diagnose (The Balance Decay Paradox)

In der Ökolopoly-Engine wird die Spielbalance (`balance_always`) nach folgender Formel berechnet:
$$\text{balance} = \frac{(\text{boxD} \times 3 + \text{Politics}) \times 10}{\text{Round} + 3}$$

Dabei ist $\text{boxD}$ ein von der Lebensqualität ($V_3$) abhängiger Faktor (max. 5) und $\text{Politics}$ ($V_7$) der politische Stabilitätswert (max. 37).

### Das mathematische Problem:
Da sich die Runde ($\text{Round}$) im Nenner befindet, **dekrmentiert** sich der Balancewert mit fortschreitender Zeit drastisch, sofern der Zähler nicht überproportional wächst.

*   **Szenario A (Frühes Scheitern in Runde 10):**
    Wenn die Lebensqualität hoch ist ($\text{boxD} = 5$) und die Politik stabil ist ($\text{Politics} = 30$), ergibt sich für Runde 10:
    $$\text{balance} = \frac{(5 \times 3 + 30) \times 10}{10 + 3} = \frac{450}{13} \approx \mathbf{34.6}$$
*   **Szenario B (Erfolgreiches Überleben bis Runde 30):**
    Selbst bei absolut perfektem Zustand in Runde 30 ($\text{boxD} = 5$, $\text{Politics} = 37$):
    $$\text{balance} = \frac{(5 \times 3 + 37) \times 10}{30 + 3} = \frac{520}{33} \approx \mathbf{15.75}$$

### Die paradoxe Konsequenz:
Wenn die Engine den Reward `reward = self.balance` bei *jedem* Spielende im Bereich der Runden 10–30 vergibt, lernt das Reinforcement Learning Modell (oder die MCTS-Suche) folgendes Muster:
> **"Es ist strategisch klüger, in Runde 10–11 gezielt zu sterben (Ertrag: ~34.6), als sich bis Runde 30 durchzukämpfen (Ertrag: ~15.75)."**

Das erklärt die kurzen Runden (4–10) und das kaputte Muster der Jules-Daten! Der Agent optimiert rein mathematisch auf einen frühen Suizid, um den verfallenden Balance-Score zu maximieren.

---

## 2. Evo-10 Lösungsansatz (Survival-Capped Balance)

Um das Paradoxon zu durchbrechen, modifizieren wir die Reward-Funktion im Environment (`src/oeko_core/envs/oeko_env.py`):

```python
# Alt (Evo-9): Belohnung bei jedem Done in Runde 10-30
if self.done and self.V[self.ROUND] in range(10, 31):
    reward = self.balance
else:
    reward = 0

# Neu (Evo-10): Belohnung NUR bei erfolgreichem Überleben der vollen 30 Runden
if self.done and self.V[self.ROUND] == 30:
    reward = self.balance
else:
    reward = 0.0
```

### Warum das funktioniert:
1.  **Überlebenspflicht (Survival Constraint):** Jedes Sterben vor Runde 30 (egal wie hoch die Balance in Runde 15 war) führt zu einem Reward von **0.0**.
2.  **Balancemaximierung (Goal Optimization):** Der Agent erhält erst in Runde 30 einen positiven Reward, welcher der tatsächlichen Spielbalance an der Ziellinie entspricht. Dies zwingt den MCTS-Planer, Pfade zu wählen, die *sowohl* 30 Runden überleben *als auch* am Ende die höchste Balance aufweisen.

---

## 3. Git- & Branch-Architektur für Evo-10

Um absolute Code-Integrität zu wahren und Jules am unkontrollierten Abweichen zu hindern, etablieren wir folgende Struktur:

1.  **Ausgangspunkt (evo9-bugfix-base):**
    Enthält die verifizierten Core-Bugfixes (Bug A+B) und unseren neuen `RecordEpisodeStatistics` Monkeypatch, der die MCTS-Suche stabilisiert.
2.  **Neuer Entwicklungszweig (feat-evo10-balance):**
    Wir erstellen lokal einen dedizierten Branch von `evo9-bugfix-base` und pushen ihn zu GitHub:
    ```powershell
    git checkout evo9-bugfix-base
    git pull origin evo9-bugfix-base
    git checkout -b feat-evo10-balance
    ```

---

## 4. Jules-Orchestrierungs-Strategie

Jules neigt dazu, standardmäßig von `main` abzuzweigen. Um dies zu verhindern, strukturieren wir das Jules-Briefing extrem strikt mit einem **Pre-Execution Check**:

1.  **Expliziter Checkout & Hard Reset:**
    Wir zwingen Jules, sich via Hash oder lokalem Upstream-Branch zu verankern:
    ```bash
    git fetch origin
    git checkout -B feat-evo10-balance origin/evo9-bugfix-base
    ```
2.  **Anti-Cheat Verifizierung:**
    Wir generieren einen dynamischen Token zur Authentifizierung des Runs.
3.  **Inkrementelle Jules-Sessions:**
    -   **Session 1 (Engine Update):** Anpassung der Reward-Logik in `oeko_env.py` auf den Survival-Capped Balance Reward + lokale Unittests.
    -   **Session 2 (Planner Sync):** Eventuelle Feineinstellung der Sovereign MCTS-Rollout-Schätzung auf die neue Reward-Struktur.
    -   **Session 3 (Benchmark Execution):** Ausführen der Multiseed-Simulationen über Seeds 0–10.

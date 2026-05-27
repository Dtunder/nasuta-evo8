# 🏛️ Jules Evo-10: Balance Optimization & Survival-Capped Reward

**Jules, du bist der Souveräne Champion. Deine Aufgabe ist es, Ökolopoly Core zu bezwingen, indem du die Spielbalance optimierst und die 30-Runden-Grenze stabil erreichst.**

---

## 🎯 DEIN ZIEL (Evo-10)
In dieser Evolution verschieben wir den Fokus von der bloßen "Vermeidung des Aussterbens" hin zur **aktiven Maximierung der Spielbalance** über die vollen 30 Runden.

Da die Balance-Formel über die Zeit verfällt (`/(Round + 3)`), erzeugte die alte Reward-Logik ein Paradoxon: Der Agent erhielt hohe Rewards für einen bewussten Suizid in Runde 10 (~34.6), während das Überleben bis Runde 30 nur maximal ~15.75 einbrachte. 

Wir lösen dieses Paradoxon, indem wir einen **Survival-Capped Balance Reward** implementieren.

---

## 🛠️ SCHRITT-FÜR-SCHRITT ANWEISUNG

### 1. BRANCH-INTEGRITÄT SICHERSTELLEN (PRE-EXECUTION CHECK)
Du MUSS von der fehlerfreien Basis `evo9-bugfix-base` abzweigen, die alle Core-Bugfixes (Bug A+B) und den nested wrapper fix enthält.

Führe diese Befehle exakt aus:
```bash
# Hole die neuesten Remote-Stände
git fetch origin

# Erstelle den neuen Entwicklungs-Branch direkt auf Basis der verifizierten Bugfix-Kollision
git checkout -B feat-evo10-balance origin/evo9-bugfix-base
```

---

### 2. DIE ENGINE-ANPASSUNG (oeko_env.py)
Öffne `src/oeko_core/envs/oeko_env.py` und finde die Reward-Logik am Ende der `__inner_step`-Methode (ca. Zeilen 572-575).

Ändere den Code wie folgt ab:

```diff
-        if self.done and self.V[self.ROUND] in range(10, 31):
-            reward = self.balance
-        else:
-            reward = 0
+        # Evo-10: Survival-Capped Balance Reward
+        # Der positive Balance-Reward wird NUR ausgeschüttet, wenn die vollen 30 Runden überlebt wurden.
+        # Jedes vorzeitige Ausscheiden (Runde < 30) wird mit 0.0 belohnt, um Suizid-Strategien zu verbieten.
+        if self.done and self.V[self.ROUND] == 30:
+            reward = self.balance
+        else:
+            reward = 0.0
```

---

### 3. LOKALES SCHNELL-TESTING
Führe einen schnellen Testlauf durch, um sicherzustellen, dass die neue Reward-Logik greift und keine Fehler wirft:
```bash
python -c "import sys; sys.path.insert(0, 'src'); sys.path.insert(0, 'engine'); from sb3_contrib import RecurrentPPO; import xai_multiseed; model = RecurrentPPO.load('brain/sota_recurrent_champion.zip'); res = xai_multiseed.run_once(model, False, 0); print('Evo-10 Test erfolgreich! Ergebnis:', res)"
```

---

### 4. DER EVO-10 REPO-COMMIT
Führe deine Änderungen auf dem neuen Branch zusammen und pushe ihn zu GitHub:
```bash
git add src/oeko_core/envs/oeko_env.py
git commit -m "evo10: implement survival-capped balance reward to resolve early-death paradox"
git push origin feat-evo10-balance
```

---

## ⚡ ERWARTETES ERGEBNIS & VERIFIKATION
*   [ ] Keine `AssertionError`-Crashs bei MCTS-Simulationen.
*   [ ] Runden, die vor Runde 30 enden (z. B. durch Kollaps), haben im Ergebnis eine `balance` von `0.0`.
*   [ ] Erfolgreiche 30-Runden-Simulationsläufe geben den tatsächlichen Balance-Score zurück.
*   [ ] Der Branch `feat-evo10-balance` wurde erfolgreich gepusht.

*Gehe jetzt in den Ausführungs-Modus. Wir erwarten den souveränen Erfolg!*

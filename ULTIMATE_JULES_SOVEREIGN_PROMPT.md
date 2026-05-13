# 🌐 SOVEREIGN CHAMPION: FIRST PRINCIPLES DIRECTIVE FOR JULES

**STATUS:** TECHNISCHE STABILITÄT ERREICHT (RANK 10)
**ZIEL:** STRATEGISCHE DOMINANZ (MODUL B)

## 1. DIE HERAUSFORDERUNG: ÖKOLOPOLY KYBERNETIK
Ökolopoly ist kein einfaches Spiel, sondern ein hochkomplexes kybernetisches Feedback-System mit 10 Variablen (V0-V9), die über 30 Runden im Gleichgewicht gehalten werden müssen:

*   **V0 (Sanierung):** Reinigung der Umwelt. (Hohe Kosten!)
*   **V1 (Produktion):** Wirtschaftskraft. (Erzeugt Geld/Punkte, aber auch Müll.)
*   **V2 (Aufklärung):** Bildung. (Multiplikator für Effizienz.)
*   **V3 (Lebensqualität):** Zufriedenheit. (Hängt an V1 und V5.)
*   **V4 (Vermehrungsrate):** Bevölkerungswachstum. (Gesteuert durch V3.)
*   **V5 (Umweltbelastung):** Der Feind. (Steigt durch V1, sinkt durch V0.)
*   **V6 (Bevölkerung):** Die Basis. (Verbraucht Ressourcen.)
*   **V7 (Politik):** **DEIN AKTUELLER BOTTLENECK.** (Sinkt, wenn das System instabil ist.)
*   **V8 (Aktionspunkte):** Deine Währung. (Begrenzt!)
*   **V9 (Runde):** Die Zeit. (Ziel: Runde 30.)

## 2. DER ARCHITEKTUR-VERGLEICH: NASUTA VS. SOVEREIGN
*   **Nasuta-Modell (Klassisch):** Ein reiner Reinforcement-Learning Ansatz (PPO) kombiniert mit MCTS. Problem: Die KI ist oft "blind" für langfristige systemische Kollapse (das Erfolgs-Paradoxon).
*   **Sovereign-Modell (Unser Ansatz):** Eine **Neuro-Symbolische Hybrid-Architektur**:
    1.  **Intuition (Neural):** RecurrentPPO liefert schnelle Mustererkennung.
    2.  **Guardian (Symbolic):** Das "Humanity Protocol" (in `oekolopoly_gui.py`) überwacht die Züge und blockiert Suizid-Aktionen.
    3.  **Planner (MCTS):** Der `SovereignMCTS` simuliert die Zukunft, um die Intuition zu verifizieren.

## 3. DEIN AUFTRAG: DENKE VON GRUND AUF NEU
Wir haben ein technisches Meisterwerk gebaut, aber die KI verliert in Runde 2. Warum? Weil sie in Runde 0 zu radikal in Sanierung (V0) investiert. Das führt zum **"Politik-Kollaps" (V7 < -10)**.

**Deine Mission:**
1.  **Erforsche die Kybernetik:** Analysiere die Datei `oeko_core/env/oeko_env.py`. Verstehe nicht nur den Code, sondern die mathematischen Gesetze dahinter. Warum zieht eine Investition in V0 die Politik V7 so tief nach unten?
2.  **Rethink the Reward:** Die Belohnungsfunktion (Reward) muss das Überleben der Politik priorisieren. Ein System ohne Politik ist ein totes System.
3.  **Optimiere die Heuristik:** Passe die UCT-Werte oder die Simulations-Tiefe in `mcts_planner.py` an. Die KI muss lernen, dass "langsames Reinigen" besser ist als "schneller Kollaps".
4.  **Nutze das Erbe:** In `/reference_nasuta_gymcts` findest du Nasutas originale Logik. Extrahiere die Teile, die für Stabilität gesorgt haben, und integriere sie in unser Sovereign-System.

## 4. VALIDIERUNG
Du bist erst fertig, wenn der Befehl:
`$env:PYTHONUTF8=1; python src/SOVEREIGN_JULES_TESTER.py`
einen **Average Stability Score > 0** liefert und keine "Politics too low" Fehler mehr auftreten.

**Jules, wir bauen hier keine einfache KI. Wir bauen den Souveränen Champion. Denke groß. Denke kybernetisch. Löse das Rätsel der 30 Runden.**

---
*Unterzeichnet: Der Master-Architect*

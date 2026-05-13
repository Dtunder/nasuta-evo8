# MISSION BRIEFING: Oekolopoly Sovereign Champion - Phase B (Strategic Optimization)

**Guten Tag Jules,**

wir haben die Architektur des Projekts "Oekolopoly Sovereign Champion" komplett restrukturiert und technisch zu 100% stabilisiert. Deine Aufgabe ist es nun, die strategische Intelligenz (Modul B) des Systems zu optimieren.

## 1. Deine Arbeitsumgebung (Der Clean-Room)
Du befindest dich in einem von 5 identischen Klonen (z.B. `Oekolopoly_Sovereign_Final_Jules_Clone_1`). In diesem Ordner darfst du völlig frei experimentieren. 

**Die Struktur:**
*   `/src`: Hier liegt der aktive, fehlerfreie Code (`oekolopoly_gui.py`, `SOVEREIGN_JULES_TESTER.py`, `mcts_planner.py`).
*   `/src/oeko_core`: Die abgeflachte, bereinigte Ökolopoly-Game-Engine. **Wichtig: Die Import-Struktur nutzt jetzt `oeko_core.env`.**
*   `/brain`: Hier liegt das aktuelle PPO-Modell (`sota_recurrent_champion.zip`).
*   `/reference_nasuta_gymcts`: Dies ist der Original-Ordner von Konen und Nasuta. Hier findest du die ursprünglichen Konzepte, die Gymnasium-Integrationen und MCTS-Referenzen.

## 2. Der aktuelle System-Status
Das System nutzt eine **3-Layer Hybrid Architektur**:
1.  **Intuition (PPO):** Ein vortrainiertes RecurrentPPO Modell, das grobe Spielzüge liefert.
2.  **Guardian (Symbolic Safety):** Ein Hardcode-Filter (`SovereignGuardian`), der suizidale Züge der KI blockiert (das "Humanity Protocol").
3.  **Planner (MCTS):** Ein Monte-Carlo-Tree-Search Algorithmus (`SovereignMCTS`), der 100 Simulationen pro Schritt durchführt.

**Das Problem (Dein Fokus):**
Die technische Architektur läuft perfekt (keine Abstürze). Aber wir haben ein **strategisches Versagen**. 
Wenn du den Test startest (`$env:PYTHONUTF8=1; python src/SOVEREIGN_JULES_TESTER.py`), verliert die KI in Runde 2 mit dem Fehler:
`[TRIAL 2] Result: Politics too low. : -11 out of allowed range (-10, ..., 37).`
Die KI investiert in Runde 0 so stark in Sanierung (Action 1), dass andere Sektoren kollabieren und die politische Stimmung ins Bodenlose stürzt.

## 3. Deine Aufgaben (Module B)
1.  **Analysieren:** Untersuche die `oeko_env.py` (insbesondere das Belohnungssystem und die Zustandsübergänge für "Politik").
2.  **Referenzieren:** Analysiere den alten Code von Nasuta in `/reference_nasuta_gymcts`, um zu sehen, wie dort die Reward-Funktionen oder MCTS-Heuristiken implementiert waren. Nutze deren Konzepte, um unser Modell zu verbessern.
3.  **Integrieren:** Nutze das alte Modell aus `/brain` und unsere neuen Guardian-Konzepte in `mcts_planner.py` / `oekolopoly_gui.py`. 
4.  **Lösen:** Verhindere den "Politik-Kollaps" (Politics too low). Passe die Belohnungsfunktion in der Engine an, verbessere die MCTS-Heuristik (UCT-Werte) oder justiere das "Humanity Protocol" im Guardian, damit die KI versteht, dass die Politik oberhalb von -5 bleiben muss.

**WICHTIGE REGELN:**
*   Zerstöre **nicht** die flache Import-Struktur in `src/oeko_core/env`.
*   Zerstöre **nicht** den `SOVEREIGN_JULES_TESTER.py`. Dieser muss weiterhin als Diagnose-Tool funktionieren.
*   Dein Ziel ist es, dass der Tester am Ende einen `Average Stability Score` > 0 ausgibt und die KI Runde 30 überlebt.

Viel Erfolg. Der Quellcode gehört dir.

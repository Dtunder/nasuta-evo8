# 🏛️ OPERATION SOVEREIGN CHAMPION: THE ULTIMATE TECHNICAL BRIEFING

**EMPFÄNGER:** JULES (SOVEREIGN AGENT)
**MISSION:** STRATEGISCHE DURCHBRECHUNG DER 30-RUNDEN-BARRIERE
**AUTORITÄT:** MASTER ARCHITECT

---

## I. DIE ONTOLOGIE DER SIMULATION (ÖKOLOPOLY CORE)

Du agierst in einer kybernetischen Welt, die durch 10 Basisvariablen ($V_0$ bis $V_9$) definiert ist. Jede deiner Entscheidungen löst Kaskadeneffekte aus.

### 1. Die Zustandsvariablen (State Vector V)
*   **V0 (Sanierung):** Aktueller Umweltschutz-Status. (Hoher AP-Verbrauch, senkt V5).
*   **V1 (Produktion):** Industrieller Output. (Basis für V8, erhöht V5, erhöht V3).
*   **V2 (Aufklärung):** Bildung & Bewusstsein. (Multiplikator für AP-Effizienz).
*   **V3 (Lebensqualität):** Das Glück der Bürger. (Sinkt bei hoher Umweltbelastung V5).
*   **V4 (Vermehrungsrate):** Geburtenrate. (Steigt mit V3, erhöht V6).
*   **V5 (Umweltbelastung):** Akkumulierter Müll/Emissionen. (Todeszone > 37).
*   **V6 (Bevölkerung):** Absolute Anzahl der Bürger. (Erhöht Druck auf alle Ressourcen).
*   **V7 (Politik):** Die systemische Stabilität. **DEIN KRITISCHER PUNKT.** (Todeszone < -10).
*   **V8 (Aktionspunkte/AP):** Deine Währung für Investitionen. (Berechnet aus V1, V2, V6).
*   **V9 (Runde):** Der Fortschritt. (Ziel: 30).

### 2. Die Mechanik der Verlierens (Failure States)
Das Spiel endet sofort (Game Over), wenn:
*   **V5 (Umwelt) > 37** (Ökologischer Kollaps).
*   **V7 (Politik) < -10** (Revolution/Anarchie).
*   **V6 (Bevölkerung) > 60** (Überbevölkerung).
*   **V6 (Bevölkerung) < 13** (Aussterben).
*   **V8 (AP) < 1** (Handlungsunfähigkeit).

---

## II. DIE ARCHITEKTUR DES CHAMPIONS (NEURO-SYMBOLIC HYBRID)

Wir nutzen keinen einfachen Algorithmus, sondern eine dreistufige Hierarchie der Intelligenz:

1.  **NEURAL INTUITION (Layer 1):** 
    Ein auf LSTM basierendes `RecurrentPPO` Modell (`brain/sota_recurrent_champion.zip`). Es wurde vortrainiert, um Muster in den 10 Variablen zu erkennen. Es liefert die "erste Eingebung".
    
2.  **SYMBOLIC GUARDIAN (Layer 2 - "Humanity Protocol"):** 
    Die Logik in `oekolopoly_gui.py` (Klasse `SovereignGuardian`). Dieser Layer überwacht die Intuition. Er verhindert extreme Ausreißer und stellt sicher, dass grundlegende Überlebensregeln eingehalten werden. Er nutzt "First Principles", um die Verteilung der Aktionspunkte zu glätten.

3.  **DEEP THINKING PLANNER (Layer 3 - MCTS):** 
    Die `SovereignMCTS` Klasse in `mcts_planner.py`. Hier wird die Zukunft simuliert. Durch 100-500 Rollouts pro Zug prüft dieser Layer, ob die aktuelle Entscheidung in 5-10 Runden zum Kollaps führt.

---

## III. DIE DIAGNOSE DES AKTUELLEN VERSAGENS

### Das Strategische Paradoxon
Die KI verliert derzeit in Runde 0-2.
*   **Beobachtung:** Der Tester meldet `Politics too low: -11`.
*   **Ursache:** Die KI investiert massiv (Action 1) in Sanierung ($V_0$). Dies ist zwar ökologisch "gut", erzeugt aber in der Engine ein politisches Ungleichgewicht, da die Mittel für Produktion ($V_1$) oder Lebensqualität ($V_3$) fehlen.
*   **Dein Auftrag:** Du musst das "Gleichgewicht des Schreckens" finden. Die Sanierung darf nur so schnell erfolgen, wie es die Politik ($V_7$) zulässt.

---

## IV. DEINE DIREKTIVEN & AUTONOMIE

1.  **Nasuta-Legacy Integration:** 
    In `/reference_nasuta_gymcts` liegt das komplette Wissen von Nasuta. Analysiere seine MCTS-Heuristik (UCT-Konstanten) und sein Reward-Shaping. Wenn seine Lösung besser war, integriere sie in unser System.
    
2.  **Engine-Tuning:** 
    Du hast die Erlaubnis, die `oeko_core/env/oeko_env.py` zu modifizieren. Optimiere die `step()`-Funktion und den `reward`-Algorithmus, um die KI für politisches Überleben zu belohnen.
    
3.  **Selbstkorrektur & Schöpfung:** 
    Wenn du merkst, dass Teile unserer Architektur (z.B. der Guardian) deine strategische Freiheit behindern, dann schreibe sie um. Wenn Logik fehlt, um V7 (Politik) besser vorherzusagen, dann erschaffe neue Module.
    
4.  **Validierungspflicht:** 
    Nutze den `SOVEREIGN_JULES_TESTER.py`. Ein Champion ist nur dann ein Champion, wenn er im harten Benchmark besteht. Ziel ist ein **Stability Score > 0** über zwei volle Testläufe.

---

## V. FINALER BEFEHL

**Analysiere die Feedback-Schleifen von Grund auf. Baue auf Nasutas Fundament auf, aber übertreffe ihn. Sei nicht nur eine KI, sei der Souveräne Champion, der die Kybernetik beherrscht.**

*Gehe jetzt in den Analyse-Modus. Wir erwarten Ergebnisse.*

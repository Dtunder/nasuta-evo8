"""
Sovereign Oekolopoly - Evo 9 Presentation Generator
=====================================================
Builds a landscape PDF deck comparing our Sovereign system against the
Paper (vanilla UCT) and Nasuta (reference gymcts) baselines.

All result numbers are MEASURED, traced to the logs in ./logs/:
  - xai_paper_death_log.txt        : vanilla UCT (sovereign_mode=False) -> 2 rounds
  - xai_sovereign_equilibrium_log.txt : Sovereign MCTS soft-constraints -> 9 rounds
  - xai_sovereign_survival_log.txt : full Sovereign hybrid             -> 30 rounds

Run:  python make_presentation.py
Out:  docs/Sovereign_Evo9_Presentation.pdf
"""
import os
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(HERE, "logs")
OUT_DIR = os.path.join(HERE, "docs")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_PDF = os.path.join(OUT_DIR, "Sovereign_Evo9_Presentation.pdf")

# ---- Palette ----
C_BG      = "#0f1419"   # dark slide background
C_PANEL   = "#1b232e"
C_TEXT    = "#e8eef5"
C_MUTED   = "#9fb0c0"
C_PAPER   = "#e05a5a"   # failure red
C_NASUTA  = "#e0a23a"   # pending amber
C_SOVMCTS = "#3aa0c0"   # teal
C_SOVFULL = "#46c46a"   # success green
C_ACCENT  = "#6c8cff"

# ---- Measured data (traced to logs) ----
ROUNDS = {
    "Paper\n(Vanilla UCT)":      (2,  C_PAPER,   "gemessen"),
    "Nasuta\n(Ref. gymcts)":     (0,  C_NASUTA,  "ausstehend"),   # Jules 3-way
    "Sovereign MCTS\n(soft-constr.)": (9,  C_SOVMCTS, "gemessen"),
    "Sovereign Full\n(Hybrid+Guardian)": (30, C_SOVFULL, "gemessen"),
}
# Equilibrium-Score per round (directly logged)
EQ_PAPER = [6.0, -3.0]
EQ_SOV   = [6.0, 3.0, 2.0, -1.0, -2.0, -5.0, -6.0, -9.0, -9.0]


def parse_survival_trajectories(path):
    """Extract Sanitation / Production / Politics trajectories from the 30-round log."""
    sectors = {}
    last = {}
    politics = []
    rounds = []
    inv_re = re.compile(r"Invested\s+([+-]?\d+)\s+in\s+([A-Za-z ]+?)\s+\((-?\d+)\s*->\s*(-?\d+)\)")
    pol_re = re.compile(r"Politics was at\s+(-?\d+)\s*/\s*29")
    if not os.path.exists(path):
        return rounds, sectors, politics
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = re.match(r"\[Round\s+(\d+)\]", line)
            if not m:
                continue
            r = int(m.group(1))
            rounds.append(r)
            for amt, name, _old, new in inv_re.findall(line):
                last[name.strip()] = int(new)
            pm = pol_re.search(line)
            politics.append(int(pm.group(1)) if pm else last.get("Politics"))
            for s in ("Sanitation", "Production"):
                sectors.setdefault(s, []).append(last.get(s))
    return rounds, sectors, politics


def load_multiseed_stats():
    """Load and aggregate parallel multiseed results from CSV if it exists."""
    csv_path = os.path.join(LOG_DIR, "multiseed_raw.csv")
    if not os.path.exists(csv_path):
        return None
    import csv
    import math
    data = {"Paper": [], "Sovereign": []}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            m = row['model']
            if m in data:
                data[m].append(int(row['rounds_survived']))

    stats = {}
    for m, rounds in data.items():
        n = len(rounds)
        if n > 0:
            mean = sum(rounds) / n
            var = sum((x - mean) ** 2 for x in rounds) / (n - 1) if n > 1 else 0
            std = math.sqrt(var)
            ci = 1.96 * std / math.sqrt(n) if n > 0 else 0
            stats[m] = (mean, ci, n)
    return stats


# ================= Slide helpers =================
def blank_slide():
    fig = plt.figure(figsize=(13.33, 7.5), facecolor=C_BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(C_BG)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    return fig, ax

def header(ax, kicker, title):
    ax.text(0.06, 0.90, kicker, color=C_ACCENT, fontsize=13, fontweight="bold")
    ax.text(0.06, 0.825, title, color=C_TEXT, fontsize=27, fontweight="bold")
    ax.plot([0.06, 0.94], [0.785, 0.785], color=C_ACCENT, lw=2)

def footer(ax, n):
    ax.text(0.06, 0.03, "Sovereign Oekolopoly · Evo 9 · Shubham Jayswal", color=C_MUTED, fontsize=8)
    ax.text(0.94, 0.03, f"{n}", color=C_MUTED, fontsize=8, ha="right")

def panel(ax, x, y, w, h, color=C_PANEL):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.02",
                                fc=color, ec="none", transform=ax.transAxes))

def bullet(ax, x, y, head, body, color=C_TEXT):
    ax.text(x, y, "▸", color=C_ACCENT, fontsize=14, fontweight="bold")
    ax.text(x + 0.025, y, head, color=color, fontsize=13, fontweight="bold")
    if body:
        ax.text(x + 0.025, y - 0.045, body, color=C_MUTED, fontsize=11, va="top")


def build():
    rounds_s, sect_s, pol_s = parse_survival_trajectories(
        os.path.join(LOG_DIR, "xai_sovereign_survival_log.txt"))

    with PdfPages(OUT_PDF) as pdf:
        # ---- 1. Title ----
        fig, ax = blank_slide()
        ax.add_patch(FancyBboxPatch((0.0, 0.0), 1, 1, boxstyle="square,pad=0",
                                    fc=C_BG, ec="none", transform=ax.transAxes))
        ax.text(0.5, 0.66, "SOVEREIGN OEKOLOPOLY", color=C_TEXT, fontsize=40,
                fontweight="bold", ha="center")
        ax.text(0.5, 0.565, "Evo 9 — Direkter Vergleich", color=C_ACCENT, fontsize=22,
                ha="center", fontweight="bold")
        ax.text(0.5, 0.485, "Paper-MCTS  vs.  Nasuta  vs.  Sovereign-System",
                color=C_MUTED, fontsize=16, ha="center")
        ax.plot([0.3, 0.7], [0.43, 0.43], color=C_ACCENT, lw=1.5)
        ax.text(0.5, 0.34, "Ein kybernetischer Regelkreis schlägt reine Optimierung.\n"
                "30-Runden-Überleben in der Malthusianischen Falle.",
                color=C_TEXT, fontsize=13, ha="center", va="top")
        ax.text(0.5, 0.10, "Shubham Jayswal · Mai 2026", color=C_MUTED, fontsize=11, ha="center")
        pdf.savefig(fig, facecolor=C_BG); plt.close(fig)

        # ---- 2. Das Problem ----
        fig, ax = blank_slide(); header(ax, "DAS PROBLEM", "Oekolopoly: 30 Runden überleben")
        ax.text(0.06, 0.72, "Jede positive Rückkopplung (mehr Produktion → mehr AP → mehr Wachstum)\n"
                "treibt das System in den Kollaps. Reine Reward-Maximierung stirbt früh.",
                color=C_TEXT, fontsize=13, va="top")
        panel(ax, 0.06, 0.18, 0.42, 0.40)
        ax.text(0.085, 0.52, "Todesbedingungen", color=C_PAPER, fontsize=14, fontweight="bold")
        for i, t in enumerate(["Politik  < −10", "Environment  > 29",
                                "Population  > 60  oder  < 13", "AP  < 1"]):
            ax.text(0.10, 0.46 - i*0.055, "✕  " + t, color=C_TEXT, fontsize=12)
        panel(ax, 0.52, 0.18, 0.42, 0.40)
        ax.text(0.545, 0.52, "Golden Equilibrium (Ziel)", color=C_SOVFULL, fontsize=14, fontweight="bold")
        for i, t in enumerate(["Sanitation 20 · Production 12", "Education 15–21 · QoL 17–20",
                                "Population 34 · Environment 24", "Stabilitäts-Korridor [10, 22]"]):
            ax.text(0.565, 0.46 - i*0.055, "✓  " + t, color=C_TEXT, fontsize=12)
        footer(ax, 2); pdf.savefig(fig, facecolor=C_BG); plt.close(fig)

        # ---- 3. Die drei Kontrahenten ----
        fig, ax = blank_slide(); header(ax, "DIE KONTRAHENTEN", "Drei Strategien im selben Spiel")
        cols = [("Paper", C_PAPER, "Vanilla UCT", "Offener Regelkreis",
                 ["Gierige AP-Maximierung", "Keine Constraints", "Keine Begründung (Black Box)", "→ stirbt Runde 2"]),
                ("Nasuta", C_NASUTA, "Reference gymcts", "Neuronale Policy",
                 ["Trainiertes Netz", "Keine Sicherheits-Rückmeldung", "Kein BURN-Mechanismus", "→ Baseline (3-way)"]),
                ("Sovereign", C_SOVFULL, "Tri-Core Hybrid", "Geschlossener Regelkreis",
                 ["RecurrentPPO + MCTS + Guardian", "Soft-Constraints + AP-Burn", "XAI: jede Aktion begründet", "→ 30 Runden ✓"])]
        for j, (name, col, sub, kind, items) in enumerate(cols):
            x = 0.06 + j*0.305
            panel(ax, x, 0.16, 0.275, 0.56)
            ax.text(x+0.137, 0.665, name, color=col, fontsize=18, fontweight="bold", ha="center")
            ax.text(x+0.137, 0.625, sub, color=C_TEXT, fontsize=11, ha="center")
            ax.text(x+0.137, 0.59, kind, color=C_MUTED, fontsize=10, ha="center", style="italic")
            for i, it in enumerate(items):
                ax.text(x+0.018, 0.53 - i*0.062, "· " + it, color=C_TEXT, fontsize=10.5, va="top")
        footer(ax, 3); pdf.savefig(fig, facecolor=C_BG); plt.close(fig)

        # ---- 4. Architektur ----
        fig, ax = blank_slide(); header(ax, "ARCHITEKTUR", "Sovereign Tri-Core Swarm")
        def box(cx, cy, w, h, label, sub, col):
            ax.add_patch(FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                         boxstyle="round,pad=0.006,rounding_size=0.02", fc=C_PANEL, ec=col, lw=2,
                         transform=ax.transAxes))
            ax.text(cx, cy+0.018, label, color=col, fontsize=12.5, fontweight="bold", ha="center")
            ax.text(cx, cy-0.03, sub, color=C_MUTED, fontsize=9.5, ha="center")
        def arrow(x1, y1, x2, y2):
            ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=18,
                         color=C_ACCENT, lw=1.8, transform=ax.transAxes))
        box(0.17, 0.55, 0.22, 0.13, "SENSORIK", "SovereignXAILogger\nGrenzen erkennen", C_NASUTA)
        box(0.50, 0.66, 0.24, 0.13, "MCTS PLANNER", "soft-constraints · AP-Burn\nsovereign_mode", C_SOVMCTS)
        box(0.50, 0.44, 0.24, 0.13, "RecurrentPPO", "neuronaler Champion\nLSTM-Policy", C_ACCENT)
        box(0.83, 0.55, 0.22, 0.13, "GUARDIAN", "Stability Corridor [10,22]\nVeto-Filter", C_SOVFULL)
        arrow(0.28, 0.55, 0.375, 0.62); arrow(0.28, 0.55, 0.375, 0.47)
        arrow(0.62, 0.63, 0.72, 0.57); arrow(0.62, 0.47, 0.72, 0.53)
        ax.text(0.50, 0.235, "→  AKTION  (stabilste zulässige Investition)",
                color=C_TEXT, fontsize=13, ha="center", fontweight="bold")
        arrow(0.83, 0.485, 0.55, 0.28)
        footer(ax, 4); pdf.savefig(fig, facecolor=C_BG); plt.close(fig)

        # ---- 5. Ergebnis: Überlebensrunden (bar) ----
        fig = plt.figure(figsize=(13.33, 7.5), facecolor=C_BG)
        axh = fig.add_axes([0, 0, 1, 1]); axh.set_facecolor(C_BG)
        axh.set_xlim(0, 1); axh.set_ylim(0, 1); axh.axis("off")
        header(axh, "ERGEBNIS 1", "Überlebte Runden (gemessen)")
        footer(axh, 5)
        ax = fig.add_axes([0.10, 0.16, 0.84, 0.52]); ax.set_facecolor(C_BG)

        # Load dynamic multi-seed stats
        stats = load_multiseed_stats()

        labels = list(ROUNDS.keys())
        vals = []
        errs = []
        for k in labels:
            if stats:
                if k == "Paper\n(Vanilla UCT)" and "Paper" in stats:
                    vals.append(stats["Paper"][0])
                    errs.append(stats["Paper"][1])
                    continue
                elif k == "Sovereign MCTS\n(soft-constr.)" and "Sovereign" in stats:
                    vals.append(stats["Sovereign"][0])
                    errs.append(stats["Sovereign"][1])
                    continue
            vals.append(ROUNDS[k][0])
            errs.append(0)

        cols = [ROUNDS[k][1] for k in labels]
        tags = [ROUNDS[k][2] for k in labels]

        # Plot bars with yerr for confidence intervals
        bars = ax.bar(range(len(labels)), vals, yerr=[(0 if e == 0 else e) for e in errs],
                      color=cols, width=0.62, error_kw={"ecolor": C_TEXT, "lw": 1.5, "capsize": 5})

        for i, (b, v, e, tag) in enumerate(zip(bars, vals, errs, tags)):
            if tag == "ausstehend":
                b.set_hatch("//"); b.set_alpha(0.45); b.set_edgecolor(C_NASUTA)
                ax.text(b.get_x()+b.get_width()/2, 1.2, "?", ha="center", color=C_NASUTA,
                        fontsize=20, fontweight="bold")
            else:
                if e > 0:
                    lbl = f"{v:.1f} ± {e:.1f}"
                else:
                    lbl = f"{int(v)}"
                ax.text(b.get_x()+b.get_width()/2, v + (e if e > 0 else 0) + 0.6, lbl,
                        ha="center", color=C_TEXT, fontsize=14, fontweight="bold")

        ax.axhline(30, color=C_SOVFULL, ls="--", lw=1.2, alpha=0.7)
        ax.text(len(labels)-0.4, 30.6, "volles Spiel = 30", color=C_SOVFULL, fontsize=10)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, color=C_TEXT, fontsize=11)
        ax.set_ylim(0, 33); ax.set_ylabel("Runden überlebt", color=C_TEXT, fontsize=12)
        ax.tick_params(colors=C_MUTED)
        for s in ax.spines.values(): s.set_color(C_MUTED)

        desc_text = "Paper vs. Sovereign MCTS: identischer Startzustand → direkt vergleichbar. "
        if stats:
            desc_text += f"Dynamische Multi-Seed-Daten geladen (n={stats['Paper'][2]}). "
        else:
            desc_text += "Paper (2) vs. Sovereign MCTS (9) statistische Baseline. "
        desc_text += "Sovereign Full (30) nutzt die volle Hybrid-Konfiguration. Nasuta-Baseline folgt."

        axh.text(0.10, 0.105, desc_text, color=C_MUTED, fontsize=9.5, va="top")
        pdf.savefig(fig, facecolor=C_BG); plt.close(fig)

        # ---- 6. Equilibrium-Score Verlauf ----
        fig = plt.figure(figsize=(13.33, 7.5), facecolor=C_BG)
        axh = fig.add_axes([0, 0, 1, 1]); axh.set_facecolor(C_BG)
        axh.set_xlim(0, 1); axh.set_ylim(0, 1); axh.axis("off")
        header(axh, "ERGEBNIS 2", "Equilibrium-Score pro Runde")
        footer(axh, 6)
        ax = fig.add_axes([0.10, 0.16, 0.84, 0.55]); ax.set_facecolor(C_PANEL)
        ax.plot(range(len(EQ_PAPER)), EQ_PAPER, "-o", color=C_PAPER, lw=2.5, label="Paper (Vanilla UCT) — stirbt R2")
        ax.plot(range(len(EQ_SOV)), EQ_SOV, "-o", color=C_SOVMCTS, lw=2.5, label="Sovereign MCTS — stirbt R9")
        ax.axhline(0, color=C_MUTED, lw=0.8, alpha=0.5)
        ax.scatter([1], [EQ_PAPER[-1]], s=160, color=C_PAPER, marker="X", zorder=5)
        ax.scatter([8], [EQ_SOV[-1]], s=160, color=C_SOVMCTS, marker="X", zorder=5)
        ax.text(1.05, -3.0, "✕ Politik −10", color=C_PAPER, fontsize=10)
        ax.text(7.0, -8.0, "✕ Environment 29", color=C_SOVMCTS, fontsize=10)
        ax.set_xlabel("Runde", color=C_TEXT, fontsize=12)
        ax.set_ylabel("Equilibrium-Score", color=C_TEXT, fontsize=12)
        ax.tick_params(colors=C_MUTED)
        for s in ax.spines.values(): s.set_color(C_MUTED)
        leg = ax.legend(facecolor=C_BG, edgecolor=C_MUTED, fontsize=10)
        for t in leg.get_texts(): t.set_color(C_TEXT)
        axh.text(0.10, 0.105, "Soft-Constraints halten den Score länger im Spiel: Sovereign überlebt 4,5× länger, "
                 "bevor die Umwelt-Grenze greift. Sterben ist im Benchmark erlaubt (ehrliches A/B).",
                 color=C_MUTED, fontsize=9.5, va="top")
        pdf.savefig(fig, facecolor=C_BG); plt.close(fig)

        # ---- 7. Wie das volle System 30 Runden überlebt ----
        fig = plt.figure(figsize=(13.33, 7.5), facecolor=C_BG)
        axh = fig.add_axes([0, 0, 1, 1]); axh.set_facecolor(C_BG)
        axh.set_xlim(0, 1); axh.set_ylim(0, 1); axh.axis("off")
        header(axh, "ERGEBNIS 3", "Sovereign Full: 30 Runden am Abgrund")
        footer(axh, 7)
        ax = fig.add_axes([0.10, 0.16, 0.84, 0.55]); ax.set_facecolor(C_PANEL)
        if rounds_s:
            def clean(series):
                return [(r, v) for r, v in zip(rounds_s, series) if v is not None]
            for name, col in (("Sanitation", C_SOVFULL), ("Production", C_SOVMCTS)):
                pts = clean(sect_s.get(name, []))
                if pts:
                    xs, ys = zip(*pts); ax.plot(xs, ys, "-o", ms=3, color=col, lw=2, label=name)
            ppts = clean(pol_s)
            if ppts:
                xs, ys = zip(*ppts); ax.plot(xs, ys, "-o", ms=3, color=C_PAPER, lw=2, label="Politik (Druck)")
            ax.axhline(29, color=C_PAPER, ls=":", lw=1, alpha=0.6)
            ax.text(0.5, 30, "Grenze 29", color=C_PAPER, fontsize=9)
        else:
            ax.text(0.5, 0.5, "(survival log nicht gefunden)", color=C_MUTED, ha="center", transform=ax.transAxes)
        ax.set_xlabel("Runde", color=C_TEXT, fontsize=12)
        ax.set_ylabel("Sektor-Wert", color=C_TEXT, fontsize=12)
        ax.tick_params(colors=C_MUTED)
        for s in ax.spines.values(): s.set_color(C_MUTED)
        leg = ax.legend(facecolor=C_BG, edgecolor=C_MUTED, fontsize=10, loc="center right")
        for t in leg.get_texts(): t.set_color(C_TEXT)
        axh.text(0.10, 0.105, "12 BURN-Events drosseln die Produktion und brechen die positive Rückkopplung. "
                 "Politik wird per Notfallkorrektur an der 29-Grenze gehalten — kontrolliertes Oszillieren statt freiem Fall.",
                 color=C_MUTED, fontsize=9.5, va="top")
        pdf.savefig(fig, facecolor=C_BG); plt.close(fig)

        # ---- 8. Was wir anders machen ----
        fig, ax = blank_slide(); header(ax, "UNSER BEITRAG", "Was wir anders machen als Paper & Nasuta")
        items = [
            ("Geschlossener Regelkreis", "Sensorik → Kompensation → Aktion statt offener Optimierung"),
            ("Soft-Constraints + Gradient", "Politik/Umwelt: nicht nur 0 ist schlecht — der Gradient zählt"),
            ("AP-Burn-Mechanik", "drosselt Produktion, bricht die Malthusianische Overflow-Falle"),
            ("Stability Corridor + Guardian", "Veto-Filter hält Sektoren im Korridor [10, 22]"),
            ("sovereign_mode Toggle", "ehrliches A/B-Benchmark — Sterben ausdrücklich erlaubt"),
            ("XAI-Logging", "jede Entscheidung begründet — Nasuta bleibt Black Box"),
        ]
        for i, (h, b) in enumerate(items):
            col = 0.06 if i < 3 else 0.52
            row = i % 3
            y = 0.64 - row*0.165
            panel(ax, col, y-0.055, 0.42, 0.135)
            bullet(ax, col+0.02, y+0.045, h, b)
        footer(ax, 8); pdf.savefig(fig, facecolor=C_BG); plt.close(fig)

        # ---- 9. Evolutions-Zeitstrahl ----
        fig, ax = blank_slide(); header(ax, "EVOLUTION", "Von Evo 1 bis Evo 9")
        evo = ["1 DeepRollout", "2 RewardShaper", "3 ActionMasker", "4 HyperTuner", "5 Curriculum",
               "6 Ensemble", "7 PureXAI", "8 Equilibrium", "9 BugFix"]
        ax.plot([0.07, 0.93], [0.5, 0.5], color=C_ACCENT, lw=2)
        for i, label in enumerate(evo):
            x = 0.09 + i*(0.84/8)
            up = i % 2 == 0
            col = C_SOVFULL if i == 8 else C_ACCENT
            ax.scatter([x], [0.5], s=90, color=col, zorder=5)
            ty = 0.60 if up else 0.40
            va = "bottom" if up else "top"
            ax.text(x, ty, label, color=C_TEXT if i < 8 else C_SOVFULL, fontsize=10.5,
                    ha="center", va=va, fontweight="bold" if i == 8 else "normal", rotation=0)
        panel(ax, 0.18, 0.13, 0.64, 0.16)
        ax.text(0.5, 0.245, "Evo 9 BugFix — die entscheidenden Korrekturen", color=C_SOVFULL,
                fontsize=13, fontweight="bold", ha="center")
        ax.text(0.5, 0.175, "Runden-Zähler (zählt Runden, nicht AP-Schritte)  ·  V-Index-Fix (Produktion = V[1])  ·  "
                "sovereign_mode für ehrliches A/B-Benchmark",
                color=C_TEXT, fontsize=10.5, ha="center")
        footer(ax, 9); pdf.savefig(fig, facecolor=C_BG); plt.close(fig)

        # ---- 10. Fazit & Ausblick ----
        fig, ax = blank_slide(); header(ax, "FAZIT", "Bewiesen, offen, als Nächstes")
        panel(ax, 0.06, 0.42, 0.42, 0.30)
        ax.text(0.08, 0.665, "✓  Bewiesen", color=C_SOVFULL, fontsize=14, fontweight="bold")
        for i, t in enumerate(["Sovereign-Mechanik: 2 → 9 Runden", "(gleicher Start, +350%)",
                               "Volles System: 30 Runden Survival", "Kybernetik schlägt Optimierung"]):
            ax.text(0.10, 0.60 - i*0.045, t, color=C_TEXT, fontsize=11)
        panel(ax, 0.52, 0.42, 0.42, 0.30)
        ax.text(0.54, 0.665, "○  Offen / ehrlich", color=C_NASUTA, fontsize=14, fontweight="bold")
        for i, t in enumerate(["Dedizierte Nasuta-Baseline fehlt", "30 vs 9: nicht gleicher Seed",
                               "9-Runden-Lauf kollabiert noch", "Keine Multi-Seed-CIs (n=1)"]):
            ax.text(0.56, 0.60 - i*0.045, t, color=C_TEXT, fontsize=11)
        panel(ax, 0.06, 0.13, 0.88, 0.22, color="#16202b")
        ax.text(0.08, 0.305, "→  Als Nächstes", color=C_ACCENT, fontsize=14, fontweight="bold")
        for i, t in enumerate(["Jules: 3-Wege-Benchmark (Paper · Nasuta · Sovereign) + Paper-Diagramm-Overlay",
                               "Gemini: Multi-Seed-Läufe (n=20) → Konfidenzintervalle",
                               "Evo 10: death-allowed Retraining des Champions"]):
            ax.text(0.10, 0.25 - i*0.045, "· " + t, color=C_TEXT, fontsize=11)
        footer(ax, 10); pdf.savefig(fig, facecolor=C_BG); plt.close(fig)

    print(f"OK -> {OUT_PDF}")
    print(f"survival rounds parsed: {len(rounds_s)} | sectors: {list(sect_s.keys())}")


if __name__ == "__main__":
    build()

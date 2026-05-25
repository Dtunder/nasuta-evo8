"""
Sovereign Oekolopoly - Evo 9 PPTX Generator
============================================
Editable PowerPoint version of the deck. Text slides are native (editable
shapes/text); the 3 result charts + architecture diagram are embedded as
images. Data/colours are reused from make_presentation.py so numbers stay
in sync (all measured, traced to ./logs/).

Run:  python make_pptx.py
Out:  docs/Sovereign_Evo9_Presentation.pptx
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

import make_presentation as mp  # reuse colours, data, parser

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "docs")
FIG_DIR = os.path.join(OUT_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)
OUT_PPTX = os.path.join(OUT_DIR, "Sovereign_Evo9_Presentation.pptx")


def rgb(hexstr):
    return RGBColor.from_string(hexstr.lstrip("#"))

BG    = rgb(mp.C_BG)
PANEL = rgb(mp.C_PANEL)
TEXT  = rgb(mp.C_TEXT)
MUTED = rgb(mp.C_MUTED)
ACC   = rgb(mp.C_ACCENT)
PAPER = rgb(mp.C_PAPER)
NAS   = rgb(mp.C_NASUTA)
SMCTS = rgb(mp.C_SOVMCTS)
SFULL = rgb(mp.C_SOVFULL)


# ---------- matplotlib images (charts + architecture) ----------
def _dark_ax(figsize):
    fig = plt.figure(figsize=figsize, facecolor=mp.C_BG)
    ax = fig.add_axes([0.09, 0.13, 0.88, 0.80]); ax.set_facecolor(mp.C_PANEL)
    ax.tick_params(colors=mp.C_MUTED)
    for s in ax.spines.values(): s.set_color(mp.C_MUTED)
    return fig, ax

def fig_bars(path):
    fig, ax = _dark_ax((11.5, 5.0))
    labels = list(mp.ROUNDS.keys())
    vals = [mp.ROUNDS[k][0] for k in labels]
    cols = [mp.ROUNDS[k][1] for k in labels]
    tags = [mp.ROUNDS[k][2] for k in labels]
    bars = ax.bar(range(len(labels)), vals, color=cols, width=0.6)
    for b, v, tag in zip(bars, vals, tags):
        if tag == "ausstehend":
            b.set_hatch("//"); b.set_alpha(0.45); b.set_edgecolor(mp.C_NASUTA)
            ax.text(b.get_x()+b.get_width()/2, 1.2, "?", ha="center", color=mp.C_NASUTA, fontsize=20, fontweight="bold")
        else:
            ax.text(b.get_x()+b.get_width()/2, v+0.6, str(v), ha="center", color=mp.C_TEXT, fontsize=17, fontweight="bold")
    ax.axhline(30, color=mp.C_SOVFULL, ls="--", lw=1.2, alpha=0.7)
    ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, color=mp.C_TEXT, fontsize=10)
    ax.set_ylim(0, 33); ax.set_ylabel("Runden überlebt", color=mp.C_TEXT, fontsize=11)
    fig.savefig(path, facecolor=mp.C_BG, dpi=150); plt.close(fig)

def fig_equilibrium(path):
    fig, ax = _dark_ax((11.5, 5.0))
    ax.plot(range(len(mp.EQ_PAPER)), mp.EQ_PAPER, "-o", color=mp.C_PAPER, lw=2.5, label="Paper (Vanilla UCT) — stirbt R2")
    ax.plot(range(len(mp.EQ_SOV)), mp.EQ_SOV, "-o", color=mp.C_SOVMCTS, lw=2.5, label="Sovereign MCTS — stirbt R9")
    ax.axhline(0, color=mp.C_MUTED, lw=0.8, alpha=0.5)
    ax.scatter([1], [mp.EQ_PAPER[-1]], s=160, color=mp.C_PAPER, marker="X", zorder=5)
    ax.scatter([8], [mp.EQ_SOV[-1]], s=160, color=mp.C_SOVMCTS, marker="X", zorder=5)
    ax.text(1.05, -3.0, "✕ Politik −10", color=mp.C_PAPER, fontsize=10)
    ax.text(6.9, -8.0, "✕ Environment 29", color=mp.C_SOVMCTS, fontsize=10)
    ax.set_xlabel("Runde", color=mp.C_TEXT, fontsize=11); ax.set_ylabel("Equilibrium-Score", color=mp.C_TEXT, fontsize=11)
    leg = ax.legend(facecolor=mp.C_BG, edgecolor=mp.C_MUTED, fontsize=10)
    for t in leg.get_texts(): t.set_color(mp.C_TEXT)
    fig.savefig(path, facecolor=mp.C_BG, dpi=150); plt.close(fig)

def fig_survival(path):
    rounds_s, sect_s, pol_s = mp.parse_survival_trajectories(os.path.join(mp.LOG_DIR, "xai_sovereign_survival_log.txt"))
    fig, ax = _dark_ax((11.5, 5.0))
    def clean(series): return [(r, v) for r, v in zip(rounds_s, series) if v is not None]
    for name, col in (("Sanitation", mp.C_SOVFULL), ("Production", mp.C_SOVMCTS)):
        pts = clean(sect_s.get(name, []))
        if pts:
            xs, ys = zip(*pts); ax.plot(xs, ys, "-o", ms=3, color=col, lw=2, label=name)
    ppts = clean(pol_s)
    if ppts:
        xs, ys = zip(*ppts); ax.plot(xs, ys, "-o", ms=3, color=mp.C_PAPER, lw=2, label="Politik (Druck)")
    ax.axhline(29, color=mp.C_PAPER, ls=":", lw=1, alpha=0.6); ax.text(0.5, 30, "Grenze 29", color=mp.C_PAPER, fontsize=9)
    ax.set_xlabel("Runde", color=mp.C_TEXT, fontsize=11); ax.set_ylabel("Sektor-Wert", color=mp.C_TEXT, fontsize=11)
    leg = ax.legend(facecolor=mp.C_BG, edgecolor=mp.C_MUTED, fontsize=10, loc="center right")
    for t in leg.get_texts(): t.set_color(mp.C_TEXT)
    fig.savefig(path, facecolor=mp.C_BG, dpi=150); plt.close(fig)

def fig_architecture(path):
    fig = plt.figure(figsize=(11.5, 5.2), facecolor=mp.C_BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    def box(cx, cy, w, h, label, sub, col):
        ax.add_patch(FancyBboxPatch((cx-w/2, cy-h/2), w, h, boxstyle="round,pad=0.006,rounding_size=0.02",
                     fc=mp.C_PANEL, ec=col, lw=2))
        ax.text(cx, cy+0.03, label, color=col, fontsize=13, fontweight="bold", ha="center")
        ax.text(cx, cy-0.05, sub, color=mp.C_MUTED, fontsize=9.5, ha="center")
    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=18, color=mp.C_ACCENT, lw=1.8))
    box(0.17, 0.60, 0.24, 0.20, "SENSORIK", "SovereignXAILogger\nGrenzen erkennen", mp.C_NASUTA)
    box(0.50, 0.78, 0.26, 0.20, "MCTS PLANNER", "soft-constraints · AP-Burn\nsovereign_mode", mp.C_SOVMCTS)
    box(0.50, 0.42, 0.26, 0.20, "RecurrentPPO", "neuronaler Champion\nLSTM-Policy", mp.C_ACCENT)
    box(0.83, 0.60, 0.24, 0.20, "GUARDIAN", "Stability Corridor [10,22]\nVeto-Filter", mp.C_SOVFULL)
    arrow(0.29, 0.60, 0.37, 0.72); arrow(0.29, 0.60, 0.37, 0.48)
    arrow(0.63, 0.74, 0.71, 0.64); arrow(0.63, 0.46, 0.71, 0.56)
    arrow(0.83, 0.50, 0.55, 0.18)
    ax.text(0.50, 0.12, "→  AKTION  (stabilste zulässige Investition)", color=mp.C_TEXT, fontsize=13, ha="center", fontweight="bold")
    fig.savefig(path, facecolor=mp.C_BG, dpi=150); plt.close(fig)


# ---------- pptx helpers ----------
def set_bg(slide, color=BG):
    f = slide.background.fill; f.solid(); f.fore_color.rgb = color

def add_text(slide, l, t, w, h, text, size, color=TEXT, bold=False, align=PP_ALIGN.LEFT, italic=False):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run(); r.text = ln
        r.font.size = Pt(size); r.font.bold = bold; r.font.italic = italic
        r.font.color.rgb = color; r.font.name = "Segoe UI"
    return tb

def rrect(slide, l, t, w, h, fill=PANEL, line=None):
    sp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
    sp.fill.solid(); sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line; sp.line.width = Pt(1.5)
    sp.shadow.inherit = False
    return sp

def header(slide, kicker, title):
    add_text(slide, 0.55, 0.30, 11, 0.4, kicker, 13, ACC, bold=True)
    add_text(slide, 0.55, 0.62, 12, 0.8, title, 30, TEXT, bold=True)
    ln = slide.shapes.add_connector(2, Inches(0.6), Inches(1.45), Inches(12.7), Inches(1.45))
    ln.line.color.rgb = ACC; ln.line.width = Pt(2)

def footer(slide, n):
    add_text(slide, 0.55, 7.05, 8, 0.3, "Sovereign Oekolopoly · Evo 9 · Shubham Jayswal", 8, MUTED)
    add_text(slide, 12.3, 7.05, 0.8, 0.3, str(n), 8, MUTED, align=PP_ALIGN.RIGHT)

def blank(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); set_bg(s); return s


def build():
    # render images first
    p_bars = os.path.join(FIG_DIR, "bars.png");  fig_bars(p_bars)
    p_eq   = os.path.join(FIG_DIR, "equilibrium.png"); fig_equilibrium(p_eq)
    p_sv   = os.path.join(FIG_DIR, "survival.png"); fig_survival(p_sv)
    p_arch = os.path.join(FIG_DIR, "architecture.png"); fig_architecture(p_arch)

    prs = Presentation()
    prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)

    # 1 Title
    s = blank(prs)
    add_text(s, 1, 2.4, 11.3, 1.0, "SOVEREIGN OEKOLOPOLY", 40, TEXT, bold=True, align=PP_ALIGN.CENTER)
    add_text(s, 1, 3.5, 11.3, 0.6, "Evo 9 — Direkter Vergleich", 22, ACC, bold=True, align=PP_ALIGN.CENTER)
    add_text(s, 1, 4.2, 11.3, 0.5, "Paper-MCTS  vs.  Nasuta  vs.  Sovereign-System", 16, MUTED, align=PP_ALIGN.CENTER)
    add_text(s, 1, 5.0, 11.3, 0.8, "Ein kybernetischer Regelkreis schlägt reine Optimierung.\n30-Runden-Überleben in der Malthusianischen Falle.", 13, TEXT, align=PP_ALIGN.CENTER)
    add_text(s, 1, 6.4, 11.3, 0.4, "Shubham Jayswal · Mai 2026", 11, MUTED, align=PP_ALIGN.CENTER)

    # 2 Problem
    s = blank(prs); header(s, "DAS PROBLEM", "Oekolopoly: 30 Runden überleben")
    add_text(s, 0.55, 1.6, 12.2, 0.8, "Jede positive Rückkopplung (mehr Produktion → mehr AP → mehr Wachstum) treibt das System in den Kollaps. Reine Reward-Maximierung stirbt früh.", 13, TEXT)
    rrect(s, 0.6, 2.9, 5.7, 3.0)
    add_text(s, 0.85, 3.05, 5.2, 0.4, "Todesbedingungen", 14, PAPER, bold=True)
    add_text(s, 0.9, 3.6, 5.2, 2.1, "✕  Politik  < −10\n✕  Environment  > 29\n✕  Population  > 60  oder  < 13\n✕  AP  < 1", 13, TEXT)
    rrect(s, 6.9, 2.9, 5.7, 3.0)
    add_text(s, 7.15, 3.05, 5.2, 0.4, "Golden Equilibrium (Ziel)", 14, SFULL, bold=True)
    add_text(s, 7.2, 3.6, 5.2, 2.1, "✓  Sanitation 20 · Production 12\n✓  Education 15–21 · QoL 17–20\n✓  Population 34 · Environment 24\n✓  Stabilitäts-Korridor [10, 22]", 13, TEXT)
    footer(s, 2)

    # 3 Kontrahenten
    s = blank(prs); header(s, "DIE KONTRAHENTEN", "Drei Strategien im selben Spiel")
    cols = [("Paper", PAPER, "Vanilla UCT", "Offener Regelkreis",
             "· Gierige AP-Maximierung\n· Keine Constraints\n· Keine Begründung (Black Box)\n· → stirbt Runde 2"),
            ("Nasuta", NAS, "Reference gymcts", "Neuronale Policy",
             "· Trainiertes Netz\n· Keine Sicherheits-Rückmeldung\n· Kein BURN-Mechanismus\n· → Baseline (3-way)"),
            ("Sovereign", SFULL, "Tri-Core Hybrid", "Geschlossener Regelkreis",
             "· RecurrentPPO + MCTS + Guardian\n· Soft-Constraints + AP-Burn\n· XAI: jede Aktion begründet\n· → 30 Runden ✓")]
    for j, (name, col, sub, kind, items) in enumerate(cols):
        x = 0.6 + j*4.07
        rrect(s, x, 1.75, 3.8, 4.6)
        add_text(s, x, 1.95, 3.8, 0.5, name, 18, col, bold=True, align=PP_ALIGN.CENTER)
        add_text(s, x, 2.5, 3.8, 0.35, sub, 11, TEXT, align=PP_ALIGN.CENTER)
        add_text(s, x, 2.85, 3.8, 0.35, kind, 10, MUTED, italic=True, align=PP_ALIGN.CENTER)
        add_text(s, x+0.25, 3.4, 3.3, 2.7, items, 11, TEXT)
    footer(s, 3)

    # 4 Architektur (image)
    s = blank(prs); header(s, "ARCHITEKTUR", "Sovereign Tri-Core Swarm")
    s.shapes.add_picture(p_arch, Inches(1.4), Inches(1.7), width=Inches(10.5))
    footer(s, 4)

    # 5 Bars
    s = blank(prs); header(s, "ERGEBNIS 1", "Überlebte Runden (gemessen)")
    s.shapes.add_picture(p_bars, Inches(1.0), Inches(1.65), width=Inches(11.3))
    add_text(s, 0.55, 6.55, 12.2, 0.5, "Paper vs. Sovereign MCTS: identischer Startzustand → direkt vergleichbar (2 → 9, +350%). Sovereign Full (30) = volle Hybrid-Konfiguration. Nasuta folgt im 3-Wege-Lauf.", 9.5, MUTED)
    footer(s, 5)

    # 6 Equilibrium
    s = blank(prs); header(s, "ERGEBNIS 2", "Equilibrium-Score pro Runde")
    s.shapes.add_picture(p_eq, Inches(1.0), Inches(1.65), width=Inches(11.3))
    add_text(s, 0.55, 6.55, 12.2, 0.5, "Soft-Constraints halten den Score länger im Spiel: Sovereign überlebt 4,5× länger, bevor die Umwelt-Grenze greift. Sterben ist im Benchmark erlaubt (ehrliches A/B).", 9.5, MUTED)
    footer(s, 6)

    # 7 Survival
    s = blank(prs); header(s, "ERGEBNIS 3", "Sovereign Full: 30 Runden am Abgrund")
    s.shapes.add_picture(p_sv, Inches(1.0), Inches(1.65), width=Inches(11.3))
    add_text(s, 0.55, 6.55, 12.2, 0.5, "12 BURN-Events drosseln die Produktion und brechen die positive Rückkopplung. Politik wird per Notfallkorrektur an der 29-Grenze gehalten — kontrolliertes Oszillieren statt freiem Fall.", 9.5, MUTED)
    footer(s, 7)

    # 8 Differentiators
    s = blank(prs); header(s, "UNSER BEITRAG", "Was wir anders machen als Paper & Nasuta")
    items = [("Geschlossener Regelkreis", "Sensorik → Kompensation → Aktion statt offener Optimierung"),
             ("Soft-Constraints + Gradient", "Politik/Umwelt: nicht nur 0 ist schlecht — der Gradient zählt"),
             ("AP-Burn-Mechanik", "drosselt Produktion, bricht die Malthusianische Overflow-Falle"),
             ("Stability Corridor + Guardian", "Veto-Filter hält Sektoren im Korridor [10, 22]"),
             ("sovereign_mode Toggle", "ehrliches A/B-Benchmark — Sterben ausdrücklich erlaubt"),
             ("XAI-Logging", "jede Entscheidung begründet — Nasuta bleibt Black Box")]
    for i, (h, b) in enumerate(items):
        x = 0.6 + (i % 2)*6.1
        y = 1.75 + (i // 2)*1.55
        rrect(s, x, y, 5.8, 1.35)
        add_text(s, x+0.25, y+0.12, 5.4, 0.4, "▸ " + h, 13, TEXT, bold=True)
        add_text(s, x+0.25, y+0.6, 5.4, 0.7, b, 11, MUTED)
    footer(s, 8)

    # 9 Timeline
    s = blank(prs); header(s, "EVOLUTION", "Von Evo 1 bis Evo 9")
    evo = ["1 DeepRollout", "2 RewardShaper", "3 ActionMasker", "4 HyperTuner", "5 Curriculum",
           "6 Ensemble", "7 PureXAI", "8 Equilibrium", "9 BugFix"]
    line = s.shapes.add_connector(2, Inches(0.8), Inches(3.4), Inches(12.5), Inches(3.4))
    line.line.color.rgb = ACC; line.line.width = Pt(2)
    for i, label in enumerate(evo):
        x = 0.9 + i*(11.6/8)
        col = SFULL if i == 8 else ACC
        dot = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x-0.1), Inches(3.3), Inches(0.2), Inches(0.2))
        dot.fill.solid(); dot.fill.fore_color.rgb = col; dot.line.fill.background()
        ty = 2.6 if i % 2 == 0 else 3.7
        add_text(s, x-0.9, ty, 1.8, 0.5, label, 10, SFULL if i == 8 else TEXT, bold=(i == 8), align=PP_ALIGN.CENTER)
    rrect(s, 2.0, 5.0, 9.3, 1.5, fill=rgb("#16202b"))
    add_text(s, 2.0, 5.15, 9.3, 0.4, "Evo 9 BugFix — die entscheidenden Korrekturen", 13, SFULL, bold=True, align=PP_ALIGN.CENTER)
    add_text(s, 2.2, 5.65, 8.9, 0.8, "Runden-Zähler (zählt Runden, nicht AP-Schritte) · V-Index-Fix (Produktion = V[1]) · sovereign_mode für ehrliches A/B-Benchmark", 11, TEXT, align=PP_ALIGN.CENTER)
    footer(s, 9)

    # 10 Fazit
    s = blank(prs); header(s, "FAZIT", "Bewiesen, offen, als Nächstes")
    rrect(s, 0.6, 1.7, 5.7, 2.4)
    add_text(s, 0.85, 1.85, 5.2, 0.4, "✓  Bewiesen", 14, SFULL, bold=True)
    add_text(s, 0.9, 2.4, 5.2, 1.6, "· Sovereign-Mechanik: 2 → 9 Runden (+350%)\n· Volles System: 30 Runden Survival\n· Kybernetik schlägt Optimierung", 11.5, TEXT)
    rrect(s, 6.9, 1.7, 5.7, 2.4)
    add_text(s, 7.15, 1.85, 5.2, 0.4, "○  Offen / ehrlich", 14, NAS, bold=True)
    add_text(s, 7.2, 2.4, 5.2, 1.6, "· Dedizierte Nasuta-Baseline fehlt\n· 30 vs 9: nicht gleicher Seed\n· 9-Runden-Lauf kollabiert noch\n· Keine Multi-Seed-CIs (n=1)", 11.5, TEXT)
    rrect(s, 0.6, 4.35, 12.0, 2.0, fill=rgb("#16202b"))
    add_text(s, 0.85, 4.5, 11.5, 0.4, "→  Als Nächstes", 14, ACC, bold=True)
    add_text(s, 0.9, 5.05, 11.5, 1.2, "· Jules: 3-Wege-Benchmark (Paper · Nasuta · Sovereign) + Paper-Diagramm-Overlay\n· Gemini: Multi-Seed-Läufe (n=20) → Konfidenzintervalle\n· Evo 10: death-allowed Retraining des Champions", 11.5, TEXT)
    footer(s, 10)

    prs.save(OUT_PPTX)
    print(f"OK -> {OUT_PPTX}")


if __name__ == "__main__":
    build()

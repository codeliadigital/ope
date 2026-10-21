"""Genera las imágenes SVG de las preguntas con imagen (img/preguntas/).

Tiras de ECG (papel a 25 mm/s y 10 mm/mV), pupilas, tapones de tubos de analítica,
catéteres venosos periféricos y ojivas de botellas de gases medicinales.

Uso:  python tools/build_svgs.py
"""
import math
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "img", "preguntas")

# --------------------------------------------------------------------------
# ECG: 1 mm = 4 px; 25 mm/s -> 100 px/s; 10 mm/mV -> 40 px/mV
# --------------------------------------------------------------------------
PX_S, PX_MV, SECS, H = 100, 40, 8, 200
DT = 0.004
GRID = {False: 'stroke="#f6c9c9" stroke-width=".5"', True: 'stroke="#ee9a9a" stroke-width="1"'}


def sig(x):
    return 1 / (1 + math.exp(-max(-60.0, min(60.0, x))))


def g(t, mu, sigma, amp):
    return amp * math.exp(-((t - mu) ** 2) / (2 * sigma ** 2))


class Strip:
    def __init__(self):
        self.parts = []      # funciones f(t) -> mV
        self.extra = []

    def p(self, t0, amp=0.15):
        self.parts.append(lambda t, t0=t0: g(t, t0, 0.025, amp))

    def qrs(self, t0, r=1.3, wide=False, st=0.0, t_amp=0.3, inverted=False):
        s = 1 if not inverted else -1
        if wide:
            self.parts.append(lambda t, t0=t0: s * (g(t, t0, 0.035, r) - g(t, t0 + 0.08, 0.035, r * 0.45)))
            self.parts.append(lambda t, t0=t0: -s * g(t, t0 + 0.30, 0.06, 0.45))
            return
        self.parts.append(lambda t, t0=t0: g(t, t0 - 0.025, 0.008, -0.12) + g(t, t0, 0.011, r) + g(t, t0 + 0.027, 0.010, -0.3))
        if st:
            self.parts.append(lambda t, t0=t0: st * sig((t - t0 - 0.04) / 0.006) * (1 - sig((t - t0 - 0.30) / 0.03)))
        self.parts.append(lambda t, t0=t0: g(t, t0 + 0.26, 0.045, t_amp))

    def beat(self, t0, pr=0.16, **kw):
        self.p(t0 - pr)
        self.qrs(t0, **kw)

    def add(self, f):
        self.extra.append(f)

    def value(self, t):
        return sum(f(t) for f in self.parts) + sum(f(t) for f in self.extra)


def svg_ecg(strip, name, label="II"):
    w, h = PX_S * SECS, H
    base = h * 0.58
    pts = []
    t = 0.0
    while t <= SECS:
        y = base - strip.value(t) * PX_MV
        pts.append(f"{t * PX_S:.1f},{max(2, min(h - 2, y)):.1f}")
        t += DT
    grid = []
    for x in range(0, w + 1, 4):
        grid.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{h}" {GRID[x % 20 == 0]}/>')
    for y in range(0, h + 1, 4):
        grid.append(f'<line x1="0" y1="{y}" x2="{w}" y2="{y}" {GRID[y % 20 == 0]}/>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
<rect width="{w}" height="{h}" fill="#fff6f6"/>
{''.join(grid)}
<polyline points="{' '.join(pts)}" fill="none" stroke="#1b1b1b" stroke-width="1.6" stroke-linejoin="round"/>
<text x="8" y="18" font-family="Arial" font-size="14" font-weight="700" fill="#333">{label}</text>
<text x="{w - 8}" y="{h - 8}" font-family="Arial" font-size="11" fill="#666" text-anchor="end">25 mm/s · 10 mm/mV</text>
</svg>'''
    open(os.path.join(OUT, name), "w", encoding="utf-8").write(svg)


def regular(rate, start=0.35, **kw):
    s = Strip()
    rr = 60 / rate
    t = start
    while t < SECS - 0.1:
        s.beat(t, **kw)
        t += rr
    return s


def ecgs():
    random.seed(7)
    svg_ecg(regular(75), "ecg-sinusal.svg")
    svg_ecg(regular(42, start=0.5), "ecg-bradicardia.svg")
    svg_ecg(regular(130, start=0.3), "ecg-taquicardia-sinusal.svg")
    svg_ecg(regular(65, pr=0.34, start=0.5), "ecg-bav1.svg")
    svg_ecg(regular(75, st=0.35, t_amp=0.45), "ecg-elevacion-st.svg")

    # Fibrilación auricular: sin P, línea de base fibrilatoria, RR irregular
    s = Strip()
    phases = [(random.uniform(5, 8), random.uniform(0, 6), random.uniform(.03, .06)) for _ in range(5)]
    s.add(lambda t: sum(a * math.sin(2 * math.pi * f * t + ph) for f, ph, a in phases))
    t = 0.3
    while t < SECS - 0.1:
        s.qrs(t, t_amp=0.2)
        t += random.choice([0.42, 0.55, 0.7, 0.9, 0.48, 1.1, 0.62])
    svg_ecg(s, "ecg-fa.svg")

    # Flutter auricular: ondas F en dientes de sierra a 300/min, conducción 4:1
    s = Strip()
    s.add(lambda t: -0.22 * ((t * 5) % 1) + 0.11)
    t = 0.45
    while t < SECS - 0.1:
        s.qrs(t, t_amp=0.0)
        t += 0.8
    svg_ecg(s, "ecg-flutter.svg")

    # Taquicardia ventricular monomorfa: QRS anchos, regulares, ~180 lpm
    s = Strip()
    t = 0.2
    while t < SECS:
        s.qrs(t, r=1.6, wide=True)
        t += 60 / 180
    svg_ecg(s, "ecg-tv.svg")

    # Fibrilación ventricular: ondas caóticas sin QRS
    s = Strip()
    comps = [(random.uniform(3.5, 6.5), random.uniform(0, 6), random.uniform(.25, .5)) for _ in range(4)]
    s.add(lambda t: sum(a * math.sin(2 * math.pi * f * t + ph) for f, ph, a in comps) * (0.7 + 0.3 * math.sin(t * 1.3)))
    svg_ecg(s, "ecg-fv.svg")

    # Torsade de pointes: QRS anchos que giran sobre la línea de base
    s = Strip()
    s.add(lambda t: 1.3 * abs(math.sin(math.pi * t / 2.2)) * math.sin(2 * math.pi * 4 * t))
    svg_ecg(s, "ecg-torsade.svg")

    # Asistolia: línea casi plana
    s = Strip()
    s.add(lambda t: 0.03 * math.sin(2 * math.pi * 0.3 * t) + 0.01 * math.sin(2 * math.pi * 2.1 * t))
    svg_ecg(s, "ecg-asistolia.svg")

    # BAV completo: P a 90 lpm y QRS anchos a 35 lpm, disociados
    s = Strip()
    t = 0.2
    while t < SECS:
        s.p(t)
        t += 60 / 90
    t = 0.9
    while t < SECS - 0.2:
        s.qrs(t, r=1.1, wide=True)
        t += 60 / 35
    svg_ecg(s, "ecg-bav3.svg")

    # BAV 2.º grado Mobitz I (Wenckebach): PR que se alarga hasta una P bloqueada
    s = Strip()
    t = 0.4
    for cycle in range(3):
        for pr in (0.16, 0.26, 0.34):
            s.beat(t + pr, pr=pr)
            t += 0.8
        s.p(t)              # P bloqueada
        t += 0.8
    svg_ecg(s, "ecg-wenckebach.svg")

    # Extrasístole ventricular aislada con pausa compensadora
    s = Strip()
    beats = [0.4, 1.2, 2.0, 2.8, 3.35, 4.4, 5.2, 6.0, 6.8, 7.6]
    for i, t in enumerate(beats):
        if i == 4:
            s.qrs(t, r=1.7, wide=True)
        else:
            s.beat(t)
    svg_ecg(s, "ecg-extrasistole.svg")


# --------------------------------------------------------------------------
# Pupilas
# --------------------------------------------------------------------------
def eye(cx, r_pupil):
    return (f'<ellipse cx="{cx}" cy="70" rx="78" ry="44" fill="#fff" stroke="#333" stroke-width="3"/>'
            f'<circle cx="{cx}" cy="70" r="36" fill="#6b8e5a" stroke="#3d5a31" stroke-width="2"/>'
            f'<circle cx="{cx}" cy="70" r="{r_pupil}" fill="#111"/>'
            f'<circle cx="{cx + 10}" cy="58" r="5" fill="#fff" opacity=".8"/>')


def pupils(name, left, right):
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 140" width="420" height="140">
<rect width="420" height="140" fill="#fdf6ee"/>{eye(110, right)}{eye(310, left)}
</svg>'''
    open(os.path.join(OUT, name), "w", encoding="utf-8").write(svg)


# --------------------------------------------------------------------------
# Tubos de analítica (vacío), catéteres y botellas
# --------------------------------------------------------------------------
def tube(name, cap, cap2=None, gel=False):
    ring = f'<rect x="58" y="34" width="64" height="10" fill="{cap2}"/>' if cap2 else ''
    gel_el = '<rect x="64" y="220" width="52" height="16" fill="#e8e3c8"/>' if gel else ''
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 320" width="180" height="320">
<rect width="180" height="320" fill="#f3f6fa"/>
<rect x="64" y="70" width="52" height="210" rx="4" fill="#eef4f9" stroke="#9fb3c4" stroke-width="2"/>
<path d="M64 270 q26 30 52 0" fill="#eef4f9" stroke="#9fb3c4" stroke-width="2"/>
<rect x="66" y="150" width="48" height="120" fill="#b7202a" opacity=".85"/>
<path d="M66 268 q24 26 48 0z" fill="#b7202a" opacity=".85"/>{gel_el}
<rect x="76" y="100" width="28" height="44" fill="#fff" stroke="#c9d3dd"/>
<text x="90" y="128" font-family="Arial" font-size="16" text-anchor="middle" fill="#567">?</text>
<rect x="56" y="18" width="68" height="58" rx="8" fill="{cap}" stroke="#333" stroke-width="1.5"/>{ring}
<rect x="56" y="18" width="68" height="10" rx="5" fill="#000" opacity=".12"/>
</svg>'''
    open(os.path.join(OUT, name), "w", encoding="utf-8").write(svg)


def cannula(name, color):
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 160" width="420" height="160">
<rect width="420" height="160" fill="#f3f6fa"/>
<line x1="250" y1="80" x2="405" y2="80" stroke="#9aa3ab" stroke-width="3"/>
<path d="M250 76 L330 78 L330 82 L250 84 z" fill="#d6dde3" opacity=".9"/>
<path d="M170 80 L215 20 L245 22 L232 80 L245 138 L215 140 z" fill="{color}" stroke="#333" stroke-width="1.5"/>
<rect x="70" y="62" width="110" height="36" rx="8" fill="{color}" stroke="#333" stroke-width="1.5"/>
<rect x="18" y="68" width="56" height="24" rx="6" fill="#f2f2f2" stroke="#666"/>
<rect x="168" y="66" width="80" height="28" rx="6" fill="{color}" stroke="#333" stroke-width="1.5"/>
</svg>'''
    open(os.path.join(OUT, name), "w", encoding="utf-8").write(svg)


def cylinder(name, shoulder, shoulder2=None):
    if shoulder2:   # ojiva en cuartos alternos
        sh = (f'<path d="M50 70 Q50 40 90 32 L90 70 z" fill="{shoulder}"/><path d="M90 32 L90 70 L130 70 Q130 40 90 32z" fill="{shoulder2}"/>')
    else:
        sh = f'<path d="M50 70 Q50 36 90 30 Q130 36 130 70 z" fill="{shoulder}"/>'
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 320" width="180" height="320">
<rect width="180" height="320" fill="#f3f6fa"/>
<rect x="78" y="8" width="24" height="26" fill="#9aa3ab" stroke="#555"/>
<rect x="50" y="66" width="80" height="240" rx="8" fill="#ffffff" stroke="#555" stroke-width="2"/>
{sh}<path d="M50 70 Q50 36 90 30 Q130 36 130 70" fill="none" stroke="#555" stroke-width="2"/>
<text x="90" y="200" font-family="Arial" font-size="22" text-anchor="middle" fill="#567">?</text>
</svg>'''
    open(os.path.join(OUT, name), "w", encoding="utf-8").write(svg)


def main():
    os.makedirs(OUT, exist_ok=True)
    ecgs()
    pupils("pupilas-miosis.svg", 4, 4)
    pupils("pupilas-midriasis.svg", 27, 27)
    pupils("pupilas-anisocoria.svg", 9, 27)     # derecha dilatada
    tube("tubo-azul.svg", "#7fb6e8")
    tube("tubo-morado.svg", "#7b3fa0")
    tube("tubo-gris.svg", "#8a8f96")
    tube("tubo-verde.svg", "#2e8b57")
    tube("tubo-negro.svg", "#1d1d1d")
    tube("tubo-amarillo.svg", "#f2c230", gel=True)
    tube("tubo-rosa.svg", "#f29cc2")
    cannula("cateter-naranja.svg", "#f08a24")
    cannula("cateter-verde.svg", "#3aa655")
    cannula("cateter-rosa.svg", "#f29cc2")
    cannula("cateter-azul.svg", "#3d7fd0")
    cannula("cateter-amarillo.svg", "#f2d230")
    cylinder("botella-oxigeno.svg", "#ffffff")
    cylinder("botella-protoxido.svg", "#2d5fb3")
    cylinder("botella-aire.svg", "#ffffff", "#1d1d1d")
    print(len(os.listdir(OUT)), "SVG en img/preguntas/")


if __name__ == "__main__":
    main()

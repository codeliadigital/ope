"""Marca en rojo (==texto==) lo SUPER importante de cada resumen: lo que cae casi siempre.

Para cada tema se eligen unas pocas líneas de la caja «Trampas de examen» (por su comienzo).
La línea entera se pone en rojo y, además, sus datos en negrita más largos se marcan
también la primera vez que aparecen en el cuerpo del resumen. Es idempotente.

Uso:  python tools/marcar_rojo.py   (y después python tools/build_pdf.py)
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "resumenes-md")

ROJO = {
    2: ["**200.000-250.000 hab.", "**NANDA** = diagnóstico"],
    3: ["El diagnóstico **de riesgo NO lleva", "Regla **3-2-2**", "Los 20 años cuentan"],
    4: ["Plan = estratégica", "Según Herzberg"],
    5: ["Una falta **grave nunca**", "La **formación continuada** es a la vez"],
    6: ["La Comisión de Docencia la preside"],
    7: ["**OR** suma resultados", "Para cribado se busca"],
    8: ["Las **GPC son fuentes secundarias**", "Agresión de una **expareja"],
    9: ["**14 años** = consentimiento", "La objeción de conciencia **nunca**"],
    10: ["Moral = **práctica**"],
    11: ["Una **mamografía de cribado**"],
    12: ["Temperatura en °C"],
    13: ["Cualitativa = **inductiva**"],
    14: ["Cribado = prevención **secundaria**"],
    15: ["Población de **derecho**", "Mortalidad infantil y materna"],
    16: ["Primera causa de muerte en niños"],
    17: ["Nirsevimab = **pasiva**"],
    18: ["Antiséptico = **tejido vivo**", "Indicador **químico** correcto"],
    19: ["Aéreo = **presión negativa**", "Retirada del EPI"],
    20: ["**KCl nunca en bolo IV**", "Lactante: IM en el **vasto externo**"],
    21: ["Inhibidor enzimático"],
    22: ["La enfermera emite **órdenes de dispensación**"],
    23: ["Realimentación = pico de insulina"],
    24: ["Fragilidad se diagnostica"],
    25: ["Residuo gástrico de **250 ml**"],
    26: ["Placenta previa: sangre", "Mastitis: **no**"],
    27: ["Menopausia = **12 meses**"],
    28: ["Ictericia en las **primeras 24 h**", "Apgar: **más puntos", "**Barlow bota**"],
    29: ["Ingestión de cáusticos", "Pasta con **1.000 ppm"],
    30: ["Estenosis de píloro"],
    31: ["**AAS prohibido", "Holliday-Segar", "Lactante atragantado"],
    32: ["**16 años** = consiente", "Bulimia:"],
    33: ["Levonorgestrel **72 h**", "1 píldora olvidada", "IVE a petición"],
    34: ["**Parte de lesiones obligatorio**", "LO 1/2004:"],
    35: ["Mantoux:", "PPE VIH:", "*C. difficile*:"],
    36: ["Sedación: solo con síntoma", "Kübler-Ross"],
    37: ["Selye:", "Precontemplación"],
    38: ["Litio **0,6-1,2**", "**Intento previo**", "Distonía aguda"],
    39: ["Glasgow **≤ 8**", "Cincinnati:", "Broca (frontal)"],
    40: ["EPOC: **FEV1/FVC", "Drenaje pleural:", "Kussmaul = **cetoacidosis**"],
    41: ["SCA: ECG **≤ 10 min**", "FV/TV sin pulso", "ECG: **V1"],
    42: ["**Sangre en el meato", "Balón con **agua destilada**"],
    43: ["Cadera: **acortamiento", "Compartimental:", "Bastón en la mano"],
    44: ["Melena y posos de café", "Murphy = **colecistitis**", "Crohn:"],
    45: ["Weber: conductiva", "Colirio:", "Glaucoma agudo"],
    46: ["Neutropenia febril", "Extravasación:"],
    47: ["DM: basal **≥ 126**", "Hipoglucemia **< 70**", "Absorción: **abdomen"],
    48: ["Manchester:", "START:"],
    49: ["Wallace:", "Parkland:", "Anafilaxia:", "RCP: **30:2**"],
    50: ["Ayuno:", "Checklist:", "Profilaxis:"],
    51: ["ME: **Glasgow 3**", "Transfusión:"],
    52: ["Torácico: sello", "**Nunca pinzar**", "Aldrete"],
    53: ["Braden **6-23**", "Venosa: **maléolo", "Quemaduras: flictena"],
    54: ["Cuasi-incidente", "Centinela", "**ACR retrospectivo**"],
    55: ["Grado I **1 vez/día", "Barthel:"],
    56: ["Orden **CIN/2134/2008**", "RD **183/2008**"],
}

BOLD = re.compile(r"\*\*([^*]+)\*\*")
# Palabras demasiado comunes para buscarlas en el cuerpo
STOP = {"nunca", "siempre", "sin tope", "nada", "ninguno", "antes", "después", "primero",
        "toxicidad", "hipotensión", "hipertensión"}


def mark(n, prefixes):
    path = os.path.join(SRC, f"tema-{n:02d}.md")
    lines = open(path, encoding="utf-8").read().split("\n")
    tokens = []
    for pre in prefixes:
        hits = [i for i, l in enumerate(lines) if l.startswith("!! " + pre) or l.startswith("!! ==" + pre)]
        if len(hits) != 1:
            raise SystemExit(f"tema {n}: «{pre}» aparece {len(hits)} veces en las trampas")
        i = hits[0]
        if not lines[i].startswith("!! =="):
            lines[i] = "!! ==" + lines[i][3:] + "=="
        tokens += [t for t in BOLD.findall(lines[i]) if len(t) >= 5 and not t.lower() in STOP]
    body_marked = 0
    for t in tokens:
        tok = f"**{t}**"
        for i, l in enumerate(lines):
            if l.startswith("!!") or l.startswith("---") or ":" in l[:12] and i < 6:
                continue
            if f"=={tok}==" in l:
                break
            if tok in l:
                lines[i] = l.replace(tok, f"=={tok}==", 1)
                body_marked += 1
                break
    open(path, "w", encoding="utf-8").write("\n".join(lines))
    return len(prefixes), body_marked


def main():
    tot = [0, 0]
    for n, pre in ROJO.items():
        a, b = mark(n, pre)
        tot[0] += a
        tot[1] += b
    print(f"{tot[0]} trampas en rojo y {tot[1]} datos marcados en el cuerpo de {len(ROJO)} temas")


if __name__ == "__main__":
    main()

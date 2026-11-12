"""Quita restos del libro (cabeceras de página, pies de figura) de las preguntas EIR de los temas indicados.

Limpia tests/extra-tema-NN.json y la misma pregunta en preguntas-externas/eir-*.json (si no, repartir_eir.py la volvería a traer sucia).

Uso:  python tools/limpiar_eir.py 04 05 06   (y después python tools/build_index.py)
"""
import glob, json, re, sys

HEAD = re.compile(r"\s*PREGUNTAS DE EXAMEN CON RESPUESTA COMENTADAS \(2018-2025\) \d+")
# Cabecera de sección del libro: «35 ADMINISTRACIÓN SANITARIA», «689 ENFERMERÍA COMUNITARIA»...
SECC = re.compile(r"\s+\d{1,4}(?: [A-ZÁÉÍÓÚÜÑ]{2,}| Y){2,}(?=\s|$)")
# Cabecera de una sola palabra al final: «647 EPIDEMIOLOGÍA», «57 BIOESTADÍSTICA» (temas 11-16)
SECC1 = re.compile(r"\s+\d{1,4} [A-ZÁÉÍÓÚÜÑ]{8,}$")
# Restos de tablas o pies de figura pegados al texto: se corta desde ahí (None) o se quita (""). Revisar a mano.
FIX = {
    " Humor Estación Elemento Órgano Características": None,  # tabla de humores (tema 1)
    " Modelo de Kaiser Permanente": "",  # pie de figura (tema 2)
    " PROTOCOLO DE VACUNACIÓN FRENTE AL TÉTANOS": None,  # tabla del tétanos (tema 11)
    " MUESTRAS INDEPENDIENTES MUESTRAS APAREADAS": None,  # tabla de test estadísticos (tema 12)
}


def clean(t):
    if not isinstance(t, str):
        return t
    t = HEAD.sub("", t)
    t = SECC.sub("", t)
    t = SECC1.sub("", t)
    for k, v in FIX.items():
        i = t.find(k)
        if i >= 0:
            t = t[:i] if v is None else t.replace(k, v)
    t = re.sub(r"^1(?=Es la enfermera)", "", t)
    t = re.sub(r"^\.(?=[A-ZÁÉÍÓÚ])", "", t)
    t = re.sub(r"^[1-4](?=[A-ZÁÉÍÓÚ]{3,}[A-Za-z]*\.?$)", "", t)  # número de opción pegado: «2STROBE.» (tema 7)
    return t.strip() if t != t.strip() else t


def clean_q(p):
    old = json.dumps(p, ensure_ascii=False)
    p["q"] = clean(p["q"])
    p["o"] = [clean(o) for o in p["o"]]
    for k in ("e",):
        if k in p:
            p[k] = clean(p[k])
    if "por" in p:
        p["por"] = [clean(x) for x in p["por"]]
    return old != json.dumps(p, ensure_ascii=False)


def save(path, d, raw):
    out = json.dumps(d, ensure_ascii=False, indent=1)
    if raw.endswith("\n"):
        out += "\n"
    open(path, "w", encoding="utf-8", newline="").write(out.replace("\n", "\r\n") if "\r\n" in raw else out)


temas = sys.argv[1:]
originales = set()
for n in temas:
    path = f"tests/extra-tema-{n}.json"
    raw = open(path, encoding="utf-8", newline="").read()
    d = json.loads(raw)
    c = 0
    for p in d["preguntas"]:
        q0 = p["q"]
        if clean_q(p):
            originales.add(q0)
            c += 1
    save(path, d, raw)
    print(path, c, "limpiadas")
for path in sorted(glob.glob("preguntas-externas/eir-*.json")):
    raw = open(path, encoding="utf-8", newline="").read()
    d = json.loads(raw)
    c = 0
    for p in d["preguntas"]:
        if any(o in originales for o in [p["q"]]) or clean(p["q"]) in {clean(x) for x in originales}:
            if clean_q(p):
                c += 1
    if c:
        save(path, d, raw)
        print(path, c, "limpiadas")

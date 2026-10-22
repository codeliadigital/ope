"""Valida los tests (tests/tema-NN.json) y genera los datos que carga la web.

Genera data/temas.js (índice) y data/tests.js (todas las preguntas en un solo archivo):
los mismos datos que los .json, envueltos en un script para que la web funcione también
abriendo index.html con doble clic (file://), donde el navegador no permite leer .json
con fetch.

Uso:  python tools/build_index.py
"""
import collections
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.path.join(ROOT, "tests")
PDFS = os.path.join(ROOT, "resumenes")


def pdf_pages(path):
    try:
        import pymupdf
        return pymupdf.open(path).page_count
    except Exception:
        return None


def validate(path):
    data = json.load(open(path, encoding="utf-8"))
    errs = []
    preg = data.get("preguntas", [])
    if len(preg) < 30:
        errs.append(f"tiene {len(preg)} preguntas (se esperaban al menos 30)")
    seen = set()
    for i, p in enumerate(preg, 1):
        if len(p.get("o", [])) != 4:
            errs.append(f"P{i}: no tiene 4 opciones")
        if p.get("a") not in (0, 1, 2, 3):
            errs.append(f"P{i}: respuesta fuera de rango")
        if not p.get("q") or not p.get("e"):
            errs.append(f"P{i}: falta enunciado o explicación")
        if p.get("img") and not os.path.exists(os.path.join(ROOT, p["img"])):
            errs.append(f"P{i}: no existe la imagen {p['img']}")
        if len(set(p.get("o", []))) != len(p.get("o", [])):
            errs.append(f"P{i}: opciones repetidas")
        key = p.get("q", "").strip().lower()
        if key in seen:
            errs.append(f"P{i}: enunciado duplicado")
        seen.add(key)
    dist = collections.Counter("abcd"[p["a"]] for p in preg if p.get("a") in (0, 1, 2, 3))
    if preg and max(dist.values()) > max(10, round(len(preg) * 0.36)):
        errs.append(f"reparto de respuestas desequilibrado {dict(dist)}")
    return data, errs, dist


def write_js(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def main():
    temas, tests, failed = [], {}, False
    for f in sorted(os.listdir(TESTS)):
        if not re.match(r"tema-\d\d\.json$", f):
            continue
        data, errs, dist = validate(os.path.join(TESTS, f))
        n = data["tema"]
        # Preguntas añadidas (EIR, con imagen) que reparte tools/repartir_eir.py
        extra_path = os.path.join(TESTS, f"extra-tema-{n:02d}.json")
        if os.path.exists(extra_path):
            extra = json.load(open(extra_path, encoding="utf-8"))["preguntas"]
            for i, p in enumerate(extra, 1):
                if len(p.get("o", [])) != 4 or (p.get("a") not in (0, 1, 2, 3) and not p.get("anulada")):
                    errs.append(f"extra P{i}: opciones o respuesta incorrectas")
                if p.get("img") and not os.path.exists(os.path.join(ROOT, p["img"])):
                    errs.append(f"extra P{i}: no existe la imagen {p['img']}")
            data = dict(data, preguntas=data["preguntas"] + extra)
        tests[n] = data
        pdf = os.path.join(PDFS, f"tema-{n:02d}.pdf")
        status = "OK" if not errs else "ERROR: " + "; ".join(errs)
        failed |= bool(errs)
        print(f"{f}: {len(data['preguntas'])} preg. {dict(sorted(dist.items()))} {status}")
        temas.append({
            "n": n,
            "titulo": data["titulo"],
            "programa": data.get("programa", ""),
            "preguntas": len(data["preguntas"]),
            "pdf": f"resumenes/tema-{n:02d}.pdf" if os.path.exists(pdf) else None,
            "paginas": pdf_pages(pdf) if os.path.exists(pdf) else None,
        })
    temas.sort(key=lambda t: t["n"])
    write_js(os.path.join(ROOT, "data", "temas.js"),
             f"window.OPE_TEMAS = {json.dumps(temas, ensure_ascii=False, indent=1)};\n")
    write_js(os.path.join(ROOT, "data", "tests.js"),
             "window.OPE_TESTS = {\n" +
             ",\n".join(f"{n}: {json.dumps(tests[n], ensure_ascii=False)}" for n in sorted(tests)) +
             "\n};\n")
    print(f"data/temas.js y data/tests.js: {len(temas)} temas")

    # Exámenes oficiales (examenes/*.json) y cuestionarios (cuestionarios/*.json)
    extra = {}
    for folder in ("examenes", "cuestionarios"):
        items = []
        for f in sorted(os.listdir(os.path.join(ROOT, folder))):
            if not f.endswith(".json"):
                continue
            data, errs = validate_set(os.path.join(ROOT, folder, f), need_expl=folder == "cuestionarios")
            failed |= bool(errs)
            print(f"{folder}/{f}: {len(data['preguntas'])} preg. {'OK' if not errs else 'ERROR: ' + '; '.join(errs)}")
            items.append(data)
        # Más recientes primero; dentro de cada año, turno libre antes que promoción interna y extraordinarios
        # Cuestionarios sueltos antes que los agrupados (EIR por temas), estos por su número
        extra[folder] = sorted(items, key=lambda d: ("EIR" in d.get("grupo", ""), -d.get("anio", 0), "extra" in d["id"],
                                                     "-pi" in d["id"], d.get("num", 0)))
    write_js(os.path.join(ROOT, "data", "extra.js"),
             f"window.OPE_EXAMENES = {json.dumps(extra['examenes'], ensure_ascii=False)};\n"
             f"window.OPE_CUESTIONARIOS = {json.dumps(extra['cuestionarios'], ensure_ascii=False)};\n")
    print(f"data/extra.js: {len(extra['examenes'])} exámenes, {len(extra['cuestionarios'])} cuestionarios")
    sys.exit(1 if failed else 0)


def validate_set(path, need_expl):
    """Exámenes y cuestionarios: número libre de preguntas; las anuladas pueden no tener respuesta."""
    data = json.load(open(path, encoding="utf-8"))
    errs = []
    if not data.get("id") or not data.get("titulo"):
        errs.append("falta id o titulo")
    for i, p in enumerate(data.get("preguntas", []), 1):
        if len(p.get("o", [])) != 4 or not all(p["o"]):
            errs.append(f"P{i}: no tiene 4 opciones")
        if p.get("a") not in (0, 1, 2, 3) and not p.get("anulada"):
            errs.append(f"P{i}: respuesta fuera de rango")
        if not p.get("q") or (need_expl and data.get("explicadas", True) and not p.get("e")):
            errs.append(f"P{i}: falta enunciado o explicación")
        if p.get("img") and not os.path.exists(os.path.join(ROOT, p["img"])):
            errs.append(f"P{i}: no existe la imagen {p['img']}")
    return data, errs


if __name__ == "__main__":
    main()

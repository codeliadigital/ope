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
    if len(preg) != 30:
        errs.append(f"tiene {len(preg)} preguntas (se esperaban 30)")
    seen = set()
    for i, p in enumerate(preg, 1):
        if len(p.get("o", [])) != 4:
            errs.append(f"P{i}: no tiene 4 opciones")
        if p.get("a") not in (0, 1, 2, 3):
            errs.append(f"P{i}: respuesta fuera de rango")
        if not p.get("q") or not p.get("e"):
            errs.append(f"P{i}: falta enunciado o explicación")
        if len(set(p.get("o", []))) != len(p.get("o", [])):
            errs.append(f"P{i}: opciones repetidas")
        key = p.get("q", "").strip().lower()
        if key in seen:
            errs.append(f"P{i}: enunciado duplicado")
        seen.add(key)
    dist = collections.Counter("abcd"[p["a"]] for p in preg if p.get("a") in (0, 1, 2, 3))
    if preg and max(dist.values()) > 10:
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
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

"""Reparte las preguntas de preguntas-externas/ (EIR por temas, preguntas con imagen) entre los 56 temas.

Cada pregunta se compara (TF-IDF) con el resumen de los temas candidatos de su bloque
y se asigna al más parecido. El resultado va a tests/extra-tema-NN.json, que
build_index.py añade al test de cada tema detrás de las 30 preguntas propias.

Uso:  python tools/repartir_eir.py   (y después python tools/build_index.py)
"""
import collections
import json
import os
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Tema EIR (libro) -> temas candidatos del programa del SMS
CANDIDATOS = {
    1: [1, 3, 5, 6, 8, 9, 10, 55], 2: [2, 4, 11, 54], 3: [12], 4: [7, 8, 12, 13], 6: [20, 23, 25, 42, 49],
    7: [18, 19, 20, 25, 40, 41, 42, 44, 52, 53], 8: [23, 24, 25], 9: [1, 3, 9, 15, 54], 10: [20, 21, 22],
    11: [38], 12: [15, 36, 37], 13: [26, 27, 33], 14: [28, 29, 30, 31, 32], 15: [16, 36, 55],
    16: [46, 36], 17: [35], 18: [50, 51, 52], 19: [48, 49], 20: [41], 21: [40], 22: [39, 45],
    23: [42], 24: [44], 25: [47], 26: [43], 27: [53], 28: [35, 46, 51], 29: [7], 30: [11, 14, 16, 17],
    31: [11, 12, 15], 32: [2, 11, 13, 14, 16, 34],
}
# Preguntas con imagen (preguntas-externas/imagenes.json): tema según la imagen
TEMA_IMAGEN = [("ecg-fv", 49), ("ecg-asistolia", 49), ("ecg-tv", 49), ("ecg-", 41), ("pupilas-anisocoria", 39),
               ("pupilas-", 49), ("tubo-", 20), ("cateter-", 20), ("botella-", 40)]

STOP = set("""a al ante bajo con contra de del desde durante e el en entre es esta este hacia hasta la las le lo los
mas más me no o para pero por que qué se según si sin sobre su sus también un una uno unos y ya son ser
cual cuál cuales cuáles opción opciones correcta incorrecta señale indique siguiente siguientes paciente""".split())


def clean(t):
    t = re.sub(r"[*#|!=\[\]>`_]", " ", t.lower())
    return t


def main():
    temas = {}
    for n in range(1, 57):
        md = os.path.join(ROOT, "resumenes-md", f"tema-{n:02d}.md")
        test = json.load(open(os.path.join(ROOT, "tests", f"tema-{n:02d}.json"), encoding="utf-8"))
        text = open(md, encoding="utf-8").read() if os.path.exists(md) else ""
        text += " " + test["titulo"] + " " + test.get("programa", "")
        text += " " + " ".join(p["q"] + " " + " ".join(p["o"]) for p in test["preguntas"])
        temas[n] = clean(text)

    preguntas = []  # (candidatos, pregunta)
    for f in sorted(os.listdir(os.path.join(ROOT, "preguntas-externas"))):
        m = re.match(r"eir-(\d\d)\.json$", f)
        if not m:
            continue
        d = json.load(open(os.path.join(ROOT, "preguntas-externas", f), encoding="utf-8"))
        cand = CANDIDATOS[int(m.group(1))]
        preguntas += [(cand, p) for p in d["preguntas"]]
    img = os.path.join(ROOT, "preguntas-externas", "imagenes.json")
    if os.path.exists(img):
        d = json.load(open(img, encoding="utf-8"))
        for p in d["preguntas"]:
            n = next(t for k, t in TEMA_IMAGEN if k in p["img"])
            preguntas.append(([n], p))

    vec = TfidfVectorizer(stop_words=list(STOP), ngram_range=(1, 2), min_df=1, sublinear_tf=True)
    docs = [temas[n] for n in range(1, 57)]
    qtexts = [clean(p["q"] + " " + " ".join(p["o"]) + " " + p.get("e", "")) for _, p in preguntas]
    vec.fit(docs + qtexts)
    T = vec.transform(docs)
    Q = vec.transform(qtexts)
    sims = cosine_similarity(Q, T)

    por_tema = collections.defaultdict(list)
    for i, (cand, p) in enumerate(preguntas):
        best = max(cand, key=lambda n: sims[i][n - 1])
        por_tema[best].append(p)

    for n in range(1, 57):
        path = os.path.join(ROOT, "tests", f"extra-tema-{n:02d}.json")
        json.dump({"tema": n, "preguntas": por_tema.get(n, [])}, open(path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    print(len(preguntas), "preguntas repartidas:",
          " ".join(f"{n}:{len(por_tema.get(n, []))}" for n in range(1, 57)))


if __name__ == "__main__":
    main()

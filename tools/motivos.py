"""Motivos de cada opción incorrecta de los tests de los temas (campo «por» de cada pregunta).

  python tools/motivos.py ver NN            -> muestra el test del tema NN de forma compacta
  python tools/motivos.py poner NN fichero  -> añade los motivos desde un fichero de texto
                                               con líneas «número|letra|motivo»

En la corrección, la web muestra «Por qué no la b: …» para cada opción incorrecta.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from preguntas_imagen import write_test  # noqa: E402

L = "abcd"


def path(n):
    return os.path.join(ROOT, "tests", f"tema-{n:02d}.json")


def ver(n):
    sys.stdout.reconfigure(encoding="utf-8")
    d = json.load(open(path(n), encoding="utf-8"))
    for i, p in enumerate(d["preguntas"], 1):
        ops = " ".join(f"{L[j]}) {o}" for j, o in enumerate(p["o"]))
        print(f"{i}| {p['q']} || {ops} || OK={L[p['a']]} || {p['e']}")


def poner(n, fich):
    d = json.load(open(path(n), encoding="utf-8"))
    cnt = 0
    for line in open(fich, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        i, letra, motivo = line.split("|", 2)
        p = d["preguntas"][int(i) - 1]
        j = L.index(letra.strip())
        if j == p["a"]:
            raise SystemExit(f"tema {n} P{i}: la {letra} es la correcta")
        por = p.get("por") or [None] * 4
        por[j] = motivo.strip()
        p["por"] = por
        cnt += 1
    falta = [i for i, p in enumerate(d["preguntas"], 1)
             if any(j != p["a"] and not (p.get("por") or [None] * 4)[j] for j in range(4))]
    write_test(path(n), d)
    print(f"tema {n}: {cnt} motivos; preguntas sin completar: {falta or 'ninguna'}")


if __name__ == "__main__":
    if sys.argv[1] == "ver":
        ver(int(sys.argv[2]))
    else:
        poner(int(sys.argv[2]), sys.argv[3])

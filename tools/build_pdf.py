"""Genera los PDF de resumen a partir de resumenes-md/tema-NN.md.

Uso:  python tools/build_pdf.py [NN ...]   (sin argumentos: todos)

Formato del .md:
  ---
  tema: 2
  titulo: Título largo del tema
  pie: Texto corto para el pie de página
  sub: Subtítulo (bloques del resumen)
  ---
  ## A1. Sección          -> barra azul
  ### Subapartado          -> subtítulo azul en cursiva
  ## == BLOQUE B · ...     -> separador grande de bloque
  !! texto                 -> líneas seguidas = caja "TRAMPAS DE EXAMEN"
  ?? texto                 -> líneas seguidas = caja "CLAVE" (??: Título cambia el título)
  [[img: archivo.jpg | pie]] -> figura con imagen de resumenes-md/img/ y pie de foto
  ==texto==                -> negrita en rojo: lo que cae casi siempre (usar con mucha moderación)
"""
import html
import os
import re
import subprocess
import sys
import tempfile

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "resumenes-md")
OUT = os.path.join(ROOT, "resumenes")
CSS = os.path.join(ROOT, "tools", "resumen.css")
CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]

LIST_RE = re.compile(r"^\s*([-*+]|\d+\.)\s")


def inline(text):
    out = markdown.markdown(text.strip())
    return re.sub(r"^<p>(.*)</p>$", r"\1", out, flags=re.S)


def box(kind, title, items):
    lis = "".join(f"<li>{inline(i)}</li>" for i in items)
    return f'<div class="{kind}"><div class="tt">{html.escape(title)}</div><ul>{lis}</ul></div>'


TOP_RE = re.compile(r"==(?=\S)(.+?)(?<=\S)==")


def preprocess(body):
    # ==texto== -> negrita roja: lo que cae casi siempre en el examen
    body = TOP_RE.sub(lambda m: f'<strong class="top">{m.group(1).replace("**", "")}</strong>', body)
    lines = body.splitlines()
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("!! ") or line.startswith("?? ") or line.startswith("??: "):
            kind = "trampas" if line.startswith("!!") else "clave"
            title = "TRAMPAS DE EXAMEN" if kind == "trampas" else "CLAVE PARA RECORDAR"
            items = []
            prefix = "!! " if kind == "trampas" else "?? "
            while i < len(lines) and (lines[i].startswith(prefix) or (kind == "clave" and lines[i].startswith("??: "))):
                if lines[i].startswith("??: "):
                    title = lines[i][4:].strip()
                else:
                    items.append(lines[i][3:])
                i += 1
            out += ["", box(kind, title, items), ""]
            continue
        m = re.match(r"^\[\[img:\s*([^|\]]+?)\s*\|\s*(.+?)\s*\]\]$", line)
        if m:
            src = "file:///" + os.path.join(SRC, "img", m.group(1)).replace("\\", "/")
            out += ["", f'<figure><img src="{src}" alt="{html.escape(m.group(2))}">'
                        f'<figcaption>{inline(m.group(2))}</figcaption></figure>', ""]
            i += 1
            continue
        m = re.match(r"^## ==\s*(.+)$", line)
        if m:
            out += ["", f'<h2 class="bloque">{inline(m.group(1))}</h2>', ""]
            i += 1
            continue
        # python-markdown necesita línea en blanco antes de una lista
        if LIST_RE.match(line) and not line.startswith(" ") and out and out[-1].strip() \
                and not LIST_RE.match(out[-1]) and not out[-1].startswith(" "):
            out.append("")
        out.append(line)
        i += 1
    return "\n".join(out)


def parse(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    meta = {}
    for ln in m.group(1).splitlines():
        k, _, v = ln.partition(":")
        meta[k.strip()] = v.strip()
    return meta, text[m.end():]


def build(num, chrome):
    # num: número de tema o nombre de un resumen suelto (p. ej. "trampas")
    name = f"tema-{num:02d}" if isinstance(num, int) else num
    src = os.path.join(SRC, f"{name}.md")
    meta, body = parse(src)
    content = markdown.markdown(preprocess(body), extensions=["tables", "sane_lists"])
    kicker = f'Tema {meta["tema"]}' if meta.get("tema") else meta.get("kicker", "")
    pie = f'{kicker} · {meta.get("pie", "")} · Resumen OPE SMS'
    css = open(CSS, encoding="utf-8").read().replace('var(--footer, "")', '"' + pie.replace('"', "'") + '"')
    page = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>{kicker} · Resumen OPE</title><style>{css}</style></head><body>
<header class="portada"><h1>{kicker.upper()} · {html.escape(meta['titulo'])}</h1>
<p class="sub">{html.escape(meta.get('sub', ''))}</p></header>
{content}
</body></html>"""
    tmpdir = tempfile.mkdtemp(prefix="ope_pdf_")
    html_path = os.path.join(tmpdir, f"{name}.html")
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(page)
    pdf_path = os.path.join(OUT, f"{name}.pdf")
    subprocess.run([
        chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
        f"--user-data-dir={os.path.join(tmpdir, 'prof')}",
        "--allow-file-access-from-files",
        f"--print-to-pdf={pdf_path}", "file:///" + html_path.replace("\\", "/"),
    ], check=True, capture_output=True, timeout=120)
    try:
        import pymupdf
        pages = pymupdf.open(pdf_path).page_count
    except Exception:
        pages = "?"
    print(f"{name}.pdf  {pages} págs")


def main():
    chrome = next((c for c in CHROME_CANDIDATES if os.path.exists(c)), None)
    if not chrome:
        sys.exit("No se encontró Chrome ni Edge")
    nums = [int(a) if a.isdigit() else a for a in sys.argv[1:]] or sorted(
        int(f[5:7]) for f in os.listdir(SRC) if re.match(r"tema-\d\d\.md$", f))
    for n in nums:
        build(n, chrome)


if __name__ == "__main__":
    main()

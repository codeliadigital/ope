# OPE Enfermería SMS · Resúmenes y tests

Web estática con los **56 temas** de la OPE de Enfermería del Servicio Murciano de Salud:

- **Resumen en PDF** de cada tema, que se lee dentro de la propia web (visor PDF.js incluido, sin descargas).
- **Test por tema**: 30 preguntas propias con explicación más las preguntas del EIR 2018-2025 y las preguntas con imagen que corresponden a ese tema (ECG, pupilas, técnicas, anatomía). Si hay más de 30, se puede elegir: todas, 30 al azar, solo las del tema o solo las del EIR, que se corrige al final con nota con y sin penalización, revisión de fallos y opción de repetir solo los fallos.
- **Simulacro** con preguntas al azar de varios temas.
- **Exámenes**: los exámenes oficiales de la OPE de Enfermería del SMS (2019, 2022 y 2023; turno libre, promoción interna y extraordinarios; 125 preguntas) y los EIR 2021-2025 del Ministerio de Sanidad (210 preguntas con sus imágenes; modo examen de 4 h 30 min y −1/3), con su plantilla oficial, en modo examen (140 min) o sin tiempo. Las preguntas anuladas en la plantilla definitiva se marcan y no puntúan.
- **Preguntas trampa**: cuestionario de detalles de la práctica diaria (colores de tubos, catéteres, agujas, sondas, jeringas y gases, orden de extracción, ECG...) con un PDF corto de teoría (`resumenes/trampas.pdf`).

No hay servidor ni base de datos: cada persona que entra elige qué estudiar y nada se guarda.

## Estructura

| Carpeta / archivo | Contenido | Archivos | ¿Se publica? |
|---|---|---|---|
| `index.html`, `favicon.svg`, `README.md`, `.gitignore`, `.vercelignore` | Página principal y configuración | 5 | Sí (salvo el README) |
| `css/`, `js/` | Estilos, aplicación y visor PDF.js (en `js/pdfjs/`) | 5 | Sí |
| `data/` | `temas.js` (índice), `tests.js` (preguntas de los temas) y `extra.js` (exámenes y cuestionarios); los genera `tools/build_index.py` | 3 | Sí |
| `img/eir/` | Imágenes de las preguntas del EIR por temas | 62 | Sí |
| `img/eir-examen/` | Imágenes de los exámenes EIR 2021-2025 | 60 | Sí |
| `img/preguntas/` | Imágenes de las preguntas con imagen: SVG de `tools/build_svgs.py` y recortes de los resúmenes de `tools/build_crops.py` | 46 | Sí |
| `resumenes/` | Resúmenes en PDF (56 temas + teoría de las trampas) | 57 | Sí |
| `tools/` | Scripts para regenerar PDFs, imágenes y datos | 8 | No (`.vercelignore`) |
| `resumenes-md/` | Texto fuente de los resúmenes (`tema-NN.md`) y sus imágenes (`img/`) | 56 + 65 imágenes | No (`.vercelignore`) |
| `examenes/`, `cuestionarios/` | Exámenes oficiales (OPE SMS y EIR) y cuestionario de trampas (`.json`) | 11 + 1 | No (`.vercelignore`) |
| `preguntas-externas/` | Preguntas del EIR por temas y preguntas con imagen; `tools/repartir_eir.py` las reparte en `tests/extra-tema-NN.json` | 32 | No (`.vercelignore`) |
| `tests/` | Preguntas propias de cada test (`tema-NN.json`) y las añadidas (`extra-tema-NN.json`) | 112 | No (`.vercelignore`) |

`tools/`, `resumenes-md/` y `tests/` no hacen falta para que la web funcione; se suben al repositorio solo para poder editar el contenido más adelante.

## Publicar en GitHub + Vercel

1. **Crear el repositorio** en tu cuenta de GitHub (por ejemplo `ope-enfermeria`), vacío y sin README.
2. **Subir el contenido de la carpeta `ope-web`** (no la carpeta en sí, sino lo que hay dentro, para que `index.html` quede en la raíz del repositorio). Opciones:
   - **GitHub Desktop**: *File → Add local repository* → elige `ope-web` → *Publish repository*.
   - **Desde la terminal** (dentro de `ope-web`):
     ```bash
     git init
     git add .
     git commit -m "Resúmenes y tests OPE Enfermería"
     git branch -M main
     git remote add origin https://github.com/TU_USUARIO/ope-enfermeria.git
     git push -u origin main
     ```
   - **Arrastrando archivos en la web de GitHub** (*Add file → Upload files*): GitHub admite como máximo 100 archivos por subida, así que hazlo en cinco tandas, arrastrando siempre desde dentro de `ope-web` a la página principal del repositorio (si un archivo ya existe, se sustituye):
     1. Los 5 archivos sueltos y las carpetas `css`, `js`, `data`, `resumenes` y `tools` (75 archivos).
     2. Las carpetas `img`, `examenes` y `cuestionarios` (54 archivos). Con estas dos tandas la web ya funciona entera.
     3. La carpeta `tests` (56 archivos).
     4. Los 56 archivos `.md` de `resumenes-md` (entra en la carpeta en tu ordenador, selecciónalos y arrástralos dentro de la carpeta `resumenes-md` del repositorio; más fácil con GitHub Desktop).
     5. La carpeta `resumenes-md/img` (65 imágenes), del mismo modo.
3. **Vercel**: entra en [vercel.com](https://vercel.com) con tu cuenta de GitHub → *Add New… → Project* → importa el repositorio.
   - *Framework Preset*: **Other**
   - *Build Command*: vacío · *Output Directory*: vacío (raíz) · *Root Directory*: `./`
   - Pulsa **Deploy**. En un minuto tendrás una dirección `https://….vercel.app` para compartir.
4. Cada vez que subas cambios al repositorio, Vercel vuelve a publicar la web automáticamente.

## Probar en local

Basta con abrir `index.html` con doble clic. En ese modo el resumen se ve con el visor de PDF del propio navegador (Chrome, Edge o Firefox).

Para verla exactamente como quedará publicada (con el visor PDF.js, el que funciona en el móvil), arranca un servidor dentro de `ope-web`:

```bash
python -m http.server 5173
```

Y abre `http://localhost:5173`.

## Editar o añadir contenido

Requisitos: Python 3 con `markdown` y `pymupdf` (`pip install markdown pymupdf`) y Google Chrome o Microsoft Edge instalados.

- **Cambiar un resumen**: edita `resumenes-md/tema-NN.md` y regenera el PDF:
  ```bash
  python tools/build_pdf.py NN
  ```
  En el `.md`: `## ` crea una barra de sección, las tablas en formato Markdown se maquetan solas, las líneas que empiezan por `!! ` forman la caja «Trampas de examen», una línea `[[img: tema-NN-1.jpg | Pie de foto]]` inserta una imagen de `resumenes-md/img/` y `==texto==` pone el texto en **rojo** (solo para lo que cae casi siempre). Las líneas en rojo de los temas 2-56 se eligen en `tools/marcar_rojo.py`; las del tema 1 están puestas a mano en su `.md`.
- **Cambiar un test**: edita `tests/tema-NN.json`. Cada pregunta tiene `q` (enunciado), `o` (4 opciones), `a` (índice de la correcta: 0 = a, 1 = b, 2 = c, 3 = d), `e` (explicación) y, si lleva imagen, `img` (p. ej. `img/preguntas/ecg-fa.svg`). Las preguntas con imagen de los temas están en `tools/preguntas_imagen.py`, que las añade a los tests sin duplicarlas.
- **Cambiar un examen o un cuestionario**: edita `examenes/*.json` o `cuestionarios/*.json` (mismo formato que los tests, con número libre de preguntas). Opcionales: `img` (ruta de una imagen, p. ej. `img/preguntas/ecg-fa.svg`) y `anulada: true` (la pregunta se muestra pero no puntúa). Un archivo nuevo en esas carpetas aparece solo en la web.
- **Después de cualquier cambio**, valida y regenera los datos de la web:
  ```bash
  python tools/build_index.py
  ```
  Comprueba que cada test tiene al menos 30 preguntas con 4 opciones, sin duplicados, valida exámenes y cuestionarios y regenera `data/temas.js`, `data/tests.js` y `data/extra.js`. Si no lo ejecutas, la web seguirá mostrando las preguntas antiguas.
- Si cambias `js/app.js` o `css/styles.css`, sube el número de versión (`?v=…`) que aparece en `index.html` para que los navegadores no usen la versión guardada. Si cambias los datos (`data/`), sube además `DATA_V` al principio de `js/app.js` (y con ello la versión de `app.js` en `index.html`).

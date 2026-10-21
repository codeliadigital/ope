# OPE Enfermería SMS · Resúmenes y tests

Web estática con los **56 temas** de la OPE de Enfermería del Servicio Murciano de Salud:

- **Resumen en PDF** de cada tema, que se lee dentro de la propia web (visor PDF.js incluido, sin descargas).
- **Test de 30 preguntas** (a–d) por tema, que se corrige al final con nota con y sin penalización, revisión de fallos y opción de repetir solo los fallos.
- **Simulacro** con preguntas al azar de varios temas.

No hay servidor ni base de datos: cada persona que entra elige qué estudiar y nada se guarda.

## Estructura

| Carpeta / archivo | Contenido | ¿Se publica? |
|---|---|---|
| `index.html`, `favicon.svg` | Página principal | Sí |
| `css/`, `js/` | Estilos, aplicación y visor PDF.js | Sí |
| `resumenes/tema-NN.pdf` | Resúmenes en PDF (el tema 1 es el resumen propio) | Sí |
| `data/temas.js` | Índice de temas (lo genera `tools/build_index.py`) | Sí |
| `data/tests/tema-NN.json` | Preguntas de cada test (archivo que se edita) | No (`.vercelignore`) |
| `data/tests/tema-NN.js` | Las mismas preguntas en el formato que carga la web (lo genera `tools/build_index.py`) | Sí |
| `contenido/resumenes/tema-NN.md` | Texto fuente de los resúmenes | No (`.vercelignore`) |
| `tools/` | Scripts para regenerar PDFs e índice | No (`.vercelignore`) |

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
   - **Arrastrando archivos en la web de GitHub**: funciona, pero GitHub solo admite unos 100 archivos por subida; hazlo por carpetas (primero `resumenes`, luego `data`, etc.).
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

- **Cambiar un resumen**: edita `contenido/resumenes/tema-NN.md` y regenera el PDF:
  ```bash
  python tools/build_pdf.py NN
  ```
  En el `.md`: `## ` crea una barra de sección, las tablas en formato Markdown se maquetan solas y las líneas que empiezan por `!! ` forman la caja «Trampas de examen».
- **Cambiar un test**: edita `data/tests/tema-NN.json`. Cada pregunta tiene `q` (enunciado), `o` (4 opciones), `a` (índice de la correcta: 0 = a, 1 = b, 2 = c, 3 = d) y `e` (explicación).
- **Después de cualquier cambio**, valida y regenera los datos de la web:
  ```bash
  python tools/build_index.py
  ```
  Comprueba que cada test tiene 30 preguntas con 4 opciones, sin duplicados, y regenera `data/temas.js` y los `data/tests/tema-NN.js`. Si no lo ejecutas, la web seguirá mostrando las preguntas antiguas.
- Si cambias `js/app.js` o `css/styles.css`, sube el número de `?v=2` en `index.html` (por ejemplo a `?v=3`) para que los navegadores no usen la versión guardada.

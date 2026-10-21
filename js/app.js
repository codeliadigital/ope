// OPE Enfermería SMS · resúmenes en PDF y tests
// Aplicación estática: rutas con hash (#/, #/tema/N, #/tema/N/test, #/simulacro)

const app = document.getElementById('app');
const LETTERS = ['a', 'b', 'c', 'd'];
const pad = (n) => String(n).padStart(2, '0');
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// Abierta con doble clic (file://) el navegador bloquea fetch y los módulos: los datos se
// cargan como <script> y el PDF se muestra con el visor del propio navegador.
const IS_FILE = location.protocol === 'file:';

let temasPromise = null;
let testsPromise = null;
let activeQuiz = null;   // test en curso (para avisar antes de salir)
let viewer = null;       // visor PDF activo
let currentTema = null;  // { n, setTab }

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = src;
    s.onload = () => resolve();
    s.onerror = () => { s.remove(); reject(new Error(`No se pudo cargar ${src}`)); };
    document.head.appendChild(s);
  });
}

function getTemas() {
  temasPromise ??= loadScript('data/temas.js').then(() => {
    if (!window.OPE_TEMAS) throw new Error('No se pudo cargar el índice de temas');
    return window.OPE_TEMAS;
  }).catch((err) => { temasPromise = null; throw err; });
  return temasPromise;
}

// Todos los tests van en un solo archivo (data/tests.js) que se carga una vez
function getTest(n) {
  testsPromise ??= loadScript('data/tests.js').catch((err) => { testsPromise = null; throw err; });
  return testsPromise.then(() => {
    const data = window.OPE_TESTS?.[n];
    if (!data) throw new Error(`No se pudo cargar el test del tema ${n}`);
    return data;
  });
}

function shuffle(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function setNav(name) {
  document.querySelectorAll('.topnav a').forEach((a) => {
    a.classList.toggle('active', a.getAttribute('href') === `#/${name === 'temas' ? '' : name}`);
  });
}

/* ------------------------------------------------------------------ */
/* Router                                                             */
/* ------------------------------------------------------------------ */

let lastHash = location.hash;

async function route() {
  const hash = location.hash.replace(/^#/, '') || '/';
  const parts = hash.split('/').filter(Boolean);
  const temaN = parts[0] === 'tema' ? parseInt(parts[1], 10) : NaN;

  // Cambiar de pestaña dentro del mismo tema no recarga la página
  if (currentTema && temaN === currentTema.n) {
    currentTema.setTab(parts[2] === 'test' ? 'test' : 'resumen');
    lastHash = location.hash;
    return;
  }

  if (activeQuiz && activeQuiz.inProgress() &&
      !confirm('Tienes un test a medias. Si sales se perderán tus respuestas. ¿Salir igualmente?')) {
    history.replaceState(null, '', lastHash || '#/');
    return;
  }
  lastHash = location.hash;
  teardown();

  try {
    if (!Number.isNaN(temaN)) await renderTema(temaN, parts[2] === 'test' ? 'test' : 'resumen');
    else if (parts[0] === 'simulacro') await renderSimulacro();
    else await renderHome();
  } catch (err) {
    console.error(err);
    app.innerHTML = `<div class="empty">${esc(err.message || 'Algo ha fallado')}. <a href="#/">Volver al inicio</a></div>`;
  }
}

function teardown() {
  viewer?.destroy();
  viewer = null;
  activeQuiz?.destroy();
  activeQuiz = null;
  currentTema = null;
}

window.addEventListener('hashchange', route);
window.addEventListener('beforeunload', (e) => {
  if (activeQuiz && activeQuiz.inProgress()) { e.preventDefault(); e.returnValue = ''; }
});

/* ------------------------------------------------------------------ */
/* Portada                                                            */
/* ------------------------------------------------------------------ */

const normalize = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

async function renderHome() {
  setNav('temas');
  document.title = 'OPE Enfermería SMS · Resúmenes y tests';
  const temas = await getTemas();
  app.innerHTML = `
    <section class="hero">
      <h1>Resúmenes y tests de la OPE de Enfermería</h1>
      <p>${temas.length} temas del programa del Servicio Murciano de Salud. Cada tema tiene su resumen en PDF para leer aquí mismo y un test de 30 preguntas que se corrige al final.</p>
    </section>
    <div class="toolbar-home">
      <input class="search" type="search" placeholder="Buscar por número o palabra (p. ej. 17, vacunas, Ley 55/2003)…" aria-label="Buscar tema">
      <a class="btn accent" href="#/simulacro">Simulacro aleatorio</a>
    </div>
    <div class="grid"></div>`;
  const grid = app.querySelector('.grid');
  const search = app.querySelector('.search');

  const draw = () => {
    const q = normalize(search.value.trim());
    const list = temas.filter((t) => !q || String(t.n) === q || normalize(`${t.titulo} ${t.programa}`).includes(q));
    grid.innerHTML = list.length ? list.map((t) => `
      <article class="card">
        <a class="card-head" href="#/tema/${t.n}">
          <span class="card-num">${t.n}</span>
          <div>
            <h2 class="card-title">${esc(t.titulo)}</h2>
            <div class="card-meta">${t.paginas ? `Resumen de ${t.paginas} págs` : 'Resumen'} · ${t.preguntas} preguntas</div>
          </div>
        </a>
        <div class="card-actions">
          <a class="btn small" href="#/tema/${t.n}">Ver resumen</a>
          <a class="btn small primary" href="#/tema/${t.n}/test">Hacer test</a>
        </div>
      </article>`).join('') : '<div class="empty">No hay ningún tema que coincida con la búsqueda.</div>';
  };
  search.addEventListener('input', draw);
  draw();
}

/* ------------------------------------------------------------------ */
/* Página de tema                                                     */
/* ------------------------------------------------------------------ */

async function renderTema(n, tab) {
  setNav('');
  const temas = await getTemas();
  const idx = temas.findIndex((t) => t.n === n);
  if (idx < 0) throw new Error(`El tema ${n} no existe`);
  const t = temas[idx];
  const prev = temas[idx - 1];
  const next = temas[idx + 1];
  document.title = `Tema ${n} · OPE Enfermería SMS`;

  app.innerHTML = `
    <div class="crumbs">
      <a href="#/">← Todos los temas</a>
      <span class="pn">
        ${prev ? `<a class="btn small" href="#/tema/${prev.n}" title="Tema anterior">‹ ${prev.n}</a>` : ''}
        ${next ? `<a class="btn small" href="#/tema/${next.n}" title="Tema siguiente">${next.n} ›</a>` : ''}
      </span>
    </div>
    <header class="tema-head">
      <div class="kicker">Tema ${n}</div>
      <h1>${esc(t.titulo)}</h1>
      ${t.programa ? `<details><summary>Enunciado del programa</summary>${esc(t.programa)}</details>` : ''}
    </header>
    <div class="tabs" role="tablist">
      <button class="tab" role="tab" data-tab="resumen">Resumen</button>
      <button class="tab" role="tab" data-tab="test">Test · ${t.preguntas} preguntas</button>
    </div>
    <section data-panel="resumen" hidden></section>
    <section data-panel="test" hidden></section>`;

  const panels = {
    resumen: app.querySelector('[data-panel="resumen"]'),
    test: app.querySelector('[data-panel="test"]'),
  };
  let quizStarted = false;

  const setTab = (name) => {
    app.querySelectorAll('.tab').forEach((b) => b.setAttribute('aria-selected', String(b.dataset.tab === name)));
    for (const [k, el] of Object.entries(panels)) el.hidden = k !== name;
    if (name === 'resumen' && !viewer) {
      if (t.pdf) {
        viewer = new PdfViewer(panels.resumen, t.pdf, `Tema-${pad(n)}-resumen.pdf`);
        viewer.init();
      } else {
        panels.resumen.innerHTML = '<div class="empty">El resumen de este tema todavía no está disponible.</div>';
      }
    }
    if (name === 'resumen') viewer?.refit();
    if (name === 'test' && !quizStarted) {
      quizStarted = true;
      panels.test.innerHTML = '<div class="empty">Cargando test…</div>';
      getTest(n).then((data) => {
        const questions = data.preguntas.map((p, i) => ({ ...p, id: `${n}-${i}`, tema: n }));
        activeQuiz = new Quiz(panels.test, questions, { title: `Tema ${n}` });
      }).catch((err) => { panels.test.innerHTML = `<div class="empty">${esc(err.message)}</div>`; });
    }
  };

  app.querySelectorAll('.tab').forEach((b) => b.addEventListener('click', () => {
    const hash = `#/tema/${n}${b.dataset.tab === 'test' ? '/test' : ''}`;
    history.replaceState(null, '', hash);
    lastHash = hash;
    setTab(b.dataset.tab);
  }));

  currentTema = { n, setTab };
  setTab(tab);
  window.scrollTo(0, 0);
}

/* ------------------------------------------------------------------ */
/* Visor PDF (PDF.js): se ve en la propia web, también en móvil        */
/* ------------------------------------------------------------------ */

let pdfjsPromise = null;
function loadPdfjs() {
  const base = document.baseURI;
  pdfjsPromise ??= import(new URL('js/pdfjs/pdf.min.js', base).href).then((lib) => {
    lib.GlobalWorkerOptions.workerSrc = new URL('js/pdfjs/pdf.worker.min.js', base).href;
    return lib;
  }).catch((err) => { pdfjsPromise = null; throw err; });
  return pdfjsPromise;
}

class PdfViewer {
  constructor(container, url, downloadName) {
    this.container = container;
    this.url = url;
    this.downloadName = downloadName;
    this.pages = [];
    this.scale = 1;
    this.fit = true;
    this.visible = new Set();
    this.destroyed = false;
    this.onResize = this.debounce(() => this.fit && this.applyScale(this.fitScale()), 150);
    this.onScroll = () => {
      if (this.raf) return;
      this.raf = requestAnimationFrame(() => { this.raf = null; this.updatePageInfo(); });
    };
  }

  debounce(fn, ms) {
    let id;
    return () => { clearTimeout(id); id = setTimeout(fn, ms); };
  }

  async init() {
    this.container.innerHTML = `
      <div class="viewer">
        <div class="viewer-bar">
          <button class="btn icon small" data-act="out" title="Alejar" aria-label="Alejar">−</button>
          <span class="zoom">100%</span>
          <button class="btn icon small" data-act="in" title="Acercar" aria-label="Acercar">+</button>
          <button class="btn small" data-act="fit" title="Ajustar al ancho">Ajustar</button>
          <span class="pageinfo">Cargando…</span>
          <a class="btn small hide-sm" href="${esc(this.url)}" target="_blank" rel="noopener">Abrir aparte</a>
          <a class="btn small" href="${esc(this.url)}" download="${esc(this.downloadName)}">Descargar</a>
        </div>
        <div class="viewer-pages"><div class="viewer-msg">Cargando resumen…</div></div>
      </div>`;
    this.pagesEl = this.container.querySelector('.viewer-pages');
    this.zoomEl = this.container.querySelector('.zoom');
    this.infoEl = this.container.querySelector('.pageinfo');
    this.container.querySelector('[data-act="in"]').addEventListener('click', () => this.zoom(1.2));
    this.container.querySelector('[data-act="out"]').addEventListener('click', () => this.zoom(1 / 1.2));
    this.container.querySelector('[data-act="fit"]').addEventListener('click', () => { this.fit = true; this.applyScale(this.fitScale()); });

    if (IS_FILE) { this.embedNative(); return; }

    try {
      const pdfjs = await loadPdfjs();
      this.task = pdfjs.getDocument({ url: this.url });
      this.doc = await this.task.promise;
      if (this.destroyed) return;
      for (let i = 1; i <= this.doc.numPages; i++) {
        const page = await this.doc.getPage(i);
        if (this.destroyed) return;
        this.pages.push({ num: i, page, base: page.getViewport({ scale: 1 }), el: null, canvas: null, rendered: 0, renderTask: null });
      }
    } catch (err) {
      console.error(err);
      if (!this.destroyed) this.embedNative();
      return;
    }

    this.pagesEl.innerHTML = '';
    for (const p of this.pages) {
      p.el = document.createElement('div');
      p.el.className = 'pdf-page';
      p.el.dataset.num = p.num;
      p.el.innerHTML = '<div class="ph">Página ' + p.num + '</div>';
      this.pagesEl.appendChild(p.el);
    }
    this.observer = new IntersectionObserver((entries) => {
      for (const e of entries) {
        const p = this.pages[e.target.dataset.num - 1];
        if (e.isIntersecting) { this.visible.add(p); this.render(p); } else this.visible.delete(p);
      }
    }, { rootMargin: '800px 0px' });
    this.pages.forEach((p) => this.observer.observe(p.el));
    window.addEventListener('resize', this.onResize);
    window.addEventListener('scroll', this.onScroll, { passive: true });
    this.applyScale(this.fitScale());
  }

  // Sin PDF.js (web abierta como archivo local o fallo al cargarlo): visor del navegador
  embedNative() {
    this.container.querySelectorAll('[data-act], .zoom').forEach((el) => { el.hidden = true; });
    this.infoEl.textContent = '';
    this.pagesEl.classList.add('native');
    this.pagesEl.innerHTML = `
      <iframe class="viewer-frame" src="${esc(this.url)}#view=FitH" title="Resumen en PDF"></iframe>
      <div class="viewer-msg small">Si el resumen no aparece, <a href="${esc(this.url)}" target="_blank" rel="noopener">ábrelo en otra pestaña</a>.</div>`;
  }

  fitScale() {
    if (!this.pages.length) return 1;
    const width = this.pagesEl.clientWidth - (window.innerWidth < 560 ? 8 : 24);
    return Math.max(0.3, width / this.pages[0].base.width);
  }

  refit() {
    if (this.fit && this.pages.length) requestAnimationFrame(() => this.applyScale(this.fitScale()));
  }

  zoom(factor) {
    this.fit = false;
    this.applyScale(Math.min(4, Math.max(0.3, this.scale * factor)));
  }

  applyScale(scale) {
    if (!this.pages.length || this.destroyed) return;
    if (Math.abs(scale - this.scale) < 0.005 && this.pages[0].el.style.width) return;
    this.scale = scale;
    this.zoomEl.textContent = Math.round(scale * 100) + '%';
    for (const p of this.pages) {
      p.el.style.width = Math.floor(p.base.width * scale) + 'px';
      p.el.style.height = Math.floor(p.base.height * scale) + 'px';
    }
    this.visible.forEach((p) => this.render(p));
    this.updatePageInfo();
  }

  async render(p) {
    if (this.destroyed || p.rendered === this.scale) return;
    const scale = this.scale;
    p.renderTask?.cancel();
    const vp = p.page.getViewport({ scale });
    const dpr = Math.min(window.devicePixelRatio || 1, 2.5);
    const canvas = document.createElement('canvas');
    canvas.width = Math.floor(vp.width * dpr);
    canvas.height = Math.floor(vp.height * dpr);
    canvas.style.width = Math.floor(vp.width) + 'px';
    canvas.style.height = Math.floor(vp.height) + 'px';
    const task = p.page.render({
      canvasContext: canvas.getContext('2d'),
      viewport: vp,
      transform: dpr !== 1 ? [dpr, 0, 0, dpr, 0, 0] : null,
    });
    p.renderTask = task;
    try {
      await task.promise;
    } catch (err) {
      if (err?.name !== 'RenderingCancelledException') console.error(err);
      return;
    }
    if (this.destroyed || scale !== this.scale) return;
    p.el.replaceChildren(canvas);
    p.rendered = scale;
    p.renderTask = null;
  }

  updatePageInfo() {
    if (!this.pages.length) return;
    const mid = window.innerHeight * 0.45;
    let current = 1;
    for (const p of this.pages) {
      if (p.el.getBoundingClientRect().top <= mid) current = p.num; else break;
    }
    this.infoEl.textContent = `Página ${current} de ${this.pages.length}`;
  }

  destroy() {
    this.destroyed = true;
    this.observer?.disconnect();
    window.removeEventListener('resize', this.onResize);
    window.removeEventListener('scroll', this.onScroll);
    this.pages.forEach((p) => p.renderTask?.cancel());
    this.task?.destroy();
  }
}

/* ------------------------------------------------------------------ */
/* Test: se responde a ritmo propio y se corrige al final              */
/* ------------------------------------------------------------------ */

class Quiz {
  constructor(container, questions, { title, showTema = false, onNew = null } = {}) {
    this.container = container;
    this.original = questions;
    this.title = title;
    this.showTema = showTema;
    this.onNew = onNew;
    this.penalty = 1 / 3;
    this.start(questions);
    this.onKey = (e) => this.handleKey(e);
    document.addEventListener('keydown', this.onKey);
  }

  start(questions) {
    this.questions = questions;
    this.answers = new Array(questions.length).fill(null);
    this.idx = 0;
    this.finished = false;
    this.renderQuestion();
  }

  destroy() {
    document.removeEventListener('keydown', this.onKey);
  }

  inProgress() {
    return !this.finished && this.answers.some((a) => a !== null) && this.container.isConnected;
  }

  answeredCount() { return this.answers.filter((a) => a !== null).length; }

  renderQuestion() {
    const q = this.questions[this.idx];
    const total = this.questions.length;
    const answered = this.answeredCount();
    const last = this.idx === total - 1;
    this.container.innerHTML = `
      <div class="quiz">
        <div class="quiz-bar">
          <span class="quiz-count">${esc(this.title)} · ${answered} de ${total} respondidas</span>
          <span class="seg">
            <button class="btn small" data-act="shuffle" title="Empezar de nuevo con las preguntas en otro orden">Orden aleatorio</button>
            <button class="btn small accent" data-act="grade">Corregir test</button>
          </span>
        </div>
        <div class="progress"><i style="width:${(answered / total) * 100}%"></i></div>
        <div class="qcard">
          <div class="qnum">Pregunta ${this.idx + 1} de ${total}${this.showTema ? ` <span class="qtema">· Tema ${q.tema}</span>` : ''}</div>
          <p class="qtext">${esc(q.q)}</p>
          <div class="opts">
            ${q.o.map((o, i) => `
              <button class="opt" data-i="${i}" aria-pressed="${this.answers[this.idx] === i}">
                <span class="l">${LETTERS[i]}</span><span>${esc(o)}</span>
              </button>`).join('')}
          </div>
          <div class="qnav">
            <button class="btn" data-act="prev" ${this.idx === 0 ? 'disabled' : ''}>← Anterior</button>
            ${last
              ? '<button class="btn primary" data-act="grade">Corregir test</button>'
              : '<button class="btn primary" data-act="next">Siguiente →</button>'}
          </div>
        </div>
        <div class="dots">
          ${this.questions.map((_, i) => `<button class="dot${this.answers[i] !== null ? ' done' : ''}${i === this.idx ? ' cur' : ''}" data-go="${i}" aria-label="Ir a la pregunta ${i + 1}">${i + 1}</button>`).join('')}
        </div>
        <p class="hint">Puedes cambiar cualquier respuesta antes de corregir. Pulsa otra vez una opción marcada para dejarla en blanco. Atajos: teclas A-D o 1-4 para responder y flechas para moverte.</p>
      </div>`;

    this.container.querySelectorAll('.opt').forEach((b) => b.addEventListener('click', () => this.choose(+b.dataset.i)));
    this.container.querySelectorAll('.dot').forEach((b) => b.addEventListener('click', () => this.go(+b.dataset.go)));
    this.container.querySelector('[data-act="prev"]').addEventListener('click', () => this.go(this.idx - 1));
    this.container.querySelector('[data-act="next"]')?.addEventListener('click', () => this.go(this.idx + 1));
    this.container.querySelectorAll('[data-act="grade"]').forEach((b) => b.addEventListener('click', () => this.grade()));
    this.container.querySelector('[data-act="shuffle"]').addEventListener('click', () => {
      if (this.answeredCount() && !confirm('Se borrarán tus respuestas y empezarás de nuevo con las preguntas en otro orden. ¿Continuar?')) return;
      this.start(shuffle(this.questions));
    });
  }

  choose(i) {
    this.answers[this.idx] = this.answers[this.idx] === i ? null : i;
    this.renderQuestion();
  }

  go(i) {
    if (i < 0 || i >= this.questions.length) return;
    this.idx = i;
    this.renderQuestion();
    const card = this.container.querySelector('.quiz');
    if (card.getBoundingClientRect().top < 60) card.scrollIntoView({ block: 'start' });
  }

  handleKey(e) {
    if (this.finished || !this.container.isConnected || this.container.closest('[hidden]')) return;
    if (e.target.closest('input, textarea, select') || e.ctrlKey || e.metaKey || e.altKey) return;
    const k = e.key.toLowerCase();
    const map = { a: 0, b: 1, c: 2, d: 3, 1: 0, 2: 1, 3: 2, 4: 3 };
    if (k in map) { e.preventDefault(); this.choose(map[k]); }
    else if (k === 'arrowright') { e.preventDefault(); this.go(this.idx + 1); }
    else if (k === 'arrowleft') { e.preventDefault(); this.go(this.idx - 1); }
  }

  grade() {
    const blank = this.answers.filter((a) => a === null).length;
    if (blank && !confirm(blank === 1 ? 'Te queda 1 pregunta sin responder. ¿Corregir igualmente?' : `Te quedan ${blank} preguntas sin responder. ¿Corregir igualmente?`)) return;
    this.finished = true;
    this.filter = 'all';
    this.renderResults();
    this.container.scrollIntoView({ block: 'start' });
    window.scrollBy(0, -70);
  }

  results() {
    let ok = 0, ko = 0, bl = 0;
    this.questions.forEach((q, i) => {
      if (this.answers[i] === null) bl++;
      else if (this.answers[i] === q.a) ok++;
      else ko++;
    });
    return { ok, ko, bl };
  }

  renderResults() {
    const { ok, ko, bl } = this.results();
    const total = this.questions.length;
    const raw = (ok / total) * 10;
    const net = Math.max(0, ((ok - ko * this.penalty) / total) * 10);
    const fmt = (x) => x.toFixed(2).replace('.', ',');
    const state = (i) => (this.answers[i] === null ? 'bl' : this.answers[i] === this.questions[i].a ? 'ok' : 'ko');
    const fails = this.questions.filter((_, i) => state(i) !== 'ok');

    this.container.innerHTML = `
      <div class="quiz">
        <div class="score">
          <div class="score-top">
            <div><div class="nota">${fmt(raw)}<small> / 10</small></div><div class="nota-label">Nota sin penalización</div></div>
            <div><div class="nota" style="font-size:30px">${fmt(net)}<small> / 10</small></div><div class="nota-label">Nota con penalización</div></div>
          </div>
          <div class="stats">
            <span class="stat ok">${ok} ${ok === 1 ? 'acierto' : 'aciertos'}</span>
            <span class="stat ko">${ko} ${ko === 1 ? 'fallo' : 'fallos'}</span>
            <span class="stat bl">${bl} en blanco</span>
          </div>
          <label class="penal">Penalización por cada fallo:
            <select>
              <option value="0.3333" ${this.penalty > 0.3 ? 'selected' : ''}>resta 1/3 de acierto</option>
              <option value="0.25" ${this.penalty === 0.25 ? 'selected' : ''}>resta 1/4 de acierto</option>
              <option value="0" ${this.penalty === 0 ? 'selected' : ''}>sin penalización</option>
            </select>
          </label>
          <div class="actions">
            <button class="btn primary" data-act="retry">Repetir test</button>
            ${fails.length ? `<button class="btn" data-act="retry-fails">Repetir solo fallos y en blanco (${fails.length})</button>` : ''}
            ${this.onNew ? '<button class="btn" data-act="new">Nuevo simulacro</button>' : ''}
          </div>
        </div>
        <div class="dots" style="margin:0 0 14px">
          ${this.questions.map((_, i) => `<button class="dot ${state(i)}" data-jump="${i}" aria-label="Ver la pregunta ${i + 1}">${i + 1}</button>`).join('')}
        </div>
        <div class="filters" role="group" aria-label="Filtrar corrección">
          ${[['all', `Todas (${total})`], ['ko', `Fallos (${ko})`], ['bl', `En blanco (${bl})`], ['ok', `Aciertos (${ok})`]]
            .map(([k, label]) => `<button class="chip" data-f="${k}" aria-pressed="${this.filter === k}">${label}</button>`).join('')}
        </div>
        <div class="review">
          ${this.questions.map((q, i) => {
            const s = state(i);
            if (this.filter !== 'all' && this.filter !== s) return '';
            const verdict = s === 'ok' ? 'Correcta' : s === 'ko' ? `Incorrecta · marcaste la ${LETTERS[this.answers[i]]}, la correcta es la ${LETTERS[q.a]}` : `En blanco · la correcta es la ${LETTERS[q.a]}`;
            return `
              <article class="ritem ${s}" id="r-${i}">
                <div class="verdict">${i + 1}. ${verdict}${this.showTema ? ` · Tema ${q.tema}` : ''}</div>
                <p class="qtext">${esc(q.q)}</p>
                ${q.o.map((o, j) => {
                  const cls = j === q.a ? 'correct' : j === this.answers[i] ? 'wrong' : '';
                  const tag = j === q.a ? '<span class="tag">✓ correcta</span>' : j === this.answers[i] ? '<span class="tag">✗ tu respuesta</span>' : '';
                  return `<div class="ropt ${cls}"><span class="l">${LETTERS[j]})</span><span>${esc(o)}</span>${tag}</div>`;
                }).join('')}
                ${q.e ? `<div class="expl">${esc(q.e)}</div>` : ''}
              </article>`;
          }).join('') || '<div class="empty">No hay preguntas en este filtro.</div>'}
        </div>
      </div>`;

    this.container.querySelector('select').addEventListener('change', (e) => {
      this.penalty = parseFloat(e.target.value);
      this.renderResults();
    });
    this.container.querySelectorAll('.chip').forEach((b) => b.addEventListener('click', () => {
      this.filter = b.dataset.f;
      this.renderResults();
    }));
    this.container.querySelectorAll('[data-jump]').forEach((b) => b.addEventListener('click', () => {
      if (this.filter !== 'all') { this.filter = 'all'; this.renderResults(); }
      const el = this.container.querySelector(`#r-${b.dataset.jump}`);
      el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }));
    this.container.querySelector('[data-act="retry"]').addEventListener('click', () => this.start(this.original));
    this.container.querySelector('[data-act="retry-fails"]')?.addEventListener('click', () => this.start(fails));
    this.container.querySelector('[data-act="new"]')?.addEventListener('click', () => this.onNew());
  }
}

/* ------------------------------------------------------------------ */
/* Simulacro: preguntas al azar de varios temas                        */
/* ------------------------------------------------------------------ */

async function renderSimulacro() {
  setNav('simulacro');
  document.title = 'Simulacro · OPE Enfermería SMS';
  const temas = await getTemas();
  let count = 50;

  const setup = () => {
    activeQuiz?.destroy();
    activeQuiz = null;
    app.innerHTML = `
      <section class="hero">
        <h1>Simulacro aleatorio</h1>
        <p>Mezcla preguntas al azar de los temas que elijas. Se corrige al final, igual que los tests de cada tema.</p>
      </section>
      <div class="panel">
        <div class="field">
          <span class="lbl">Número de preguntas</span>
          <div class="seg">
            ${[30, 50, 100, 150].map((c) => `<button class="chip" data-c="${c}" aria-pressed="${c === count}">${c}</button>`).join('')}
          </div>
        </div>
        <div class="field">
          <span class="lbl">Temas incluidos</span>
          <div class="seg" style="margin-bottom:8px">
            <button class="btn small" data-sel="all">Todos</button>
            <button class="btn small" data-sel="none">Ninguno</button>
          </div>
          <div class="temas-pick">
            ${temas.map((t) => `<label title="${esc(t.titulo)}"><input type="checkbox" value="${t.n}" checked>${t.n}</label>`).join('')}
          </div>
        </div>
        <button class="btn primary" data-act="go">Empezar simulacro</button>
        <span class="sim-msg" style="margin-left:10px;color:var(--muted);font-size:14px"></span>
      </div>`;

    app.querySelectorAll('[data-c]').forEach((b) => b.addEventListener('click', () => {
      count = +b.dataset.c;
      app.querySelectorAll('[data-c]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
    }));
    app.querySelector('[data-sel="all"]').addEventListener('click', () => app.querySelectorAll('.temas-pick input').forEach((i) => { i.checked = true; }));
    app.querySelector('[data-sel="none"]').addEventListener('click', () => app.querySelectorAll('.temas-pick input').forEach((i) => { i.checked = false; }));
    app.querySelector('[data-act="go"]').addEventListener('click', async () => {
      const chosen = [...app.querySelectorAll('.temas-pick input:checked')].map((i) => +i.value);
      const msg = app.querySelector('.sim-msg');
      if (!chosen.length) { msg.textContent = 'Elige al menos un tema.'; return; }
      msg.textContent = 'Preparando preguntas…';
      try {
        const sets = await Promise.all(chosen.map((n) => getTest(n).then((d) => d.preguntas.map((p, i) => ({ ...p, id: `${n}-${i}`, tema: n })))));
        const pool = shuffle(sets.flat()).slice(0, count);
        app.innerHTML = `
          <section class="hero"><h1>Simulacro · ${pool.length} preguntas</h1>
          <p>${chosen.length === temas.length ? 'Todos los temas' : `Temas: ${chosen.join(', ')}`}</p></section>
          <section class="sim"></section>`;
        activeQuiz = new Quiz(app.querySelector('.sim'), pool, { title: 'Simulacro', showTema: true, onNew: setup });
        window.scrollTo(0, 0);
      } catch (err) {
        msg.textContent = err.message;
      }
    });
  };
  setup();
}

route();

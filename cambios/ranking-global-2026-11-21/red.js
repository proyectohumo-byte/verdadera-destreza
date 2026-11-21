// ---------- Ranking global (Supabase) ----------
// El juego envía, solo si el jugador lo acepta, el resultado de cada partida contra el ordenador.
// La clave "publishable" es pública por diseño: la seguridad está en la base de datos (solo se pueden
// llamar tres funciones, que validan lo que reciben; las tablas no se pueden leer ni escribir directamente).
const RED = {
  url: 'https://hbcalubchyzzxdjjgzzt.supabase.co',
  clave: 'sb_publishable_UKYAYdRbtw8sXVn4xvMsnw_NqT5WuYq',
  version: 'prueba-1',
};
const CONSENTIMIENTO = 2; // versión del aviso aceptado; si cambia lo que se recoge, se sube y se vuelve a preguntar
const CLAVE_RED = 'destreza.red'; // { id, participa: true|false|undefined, apodo, consentimiento }
const CLAVE_RED_COLA = 'destreza.redCola'; // partidas pendientes de enviar (sin conexión)
let redRegistrada = false; // la visita (y el apodo) ya se han enviado en esta sesión
let redOcupada = false;
let latidoRed = null; // temporizador del pulso

function leerRed() {
  const r = leerJSON(CLAVE_RED, null);
  return r && typeof r === 'object' ? r : {};
}
/** Participa y ha aceptado la versión actual del aviso. */
function redActiva() {
  const r = leerRed();
  return !!r.participa && r.consentimiento === CONSENTIMIENTO;
}
function guardarRed(r) {
  guardarJSON(CLAVE_RED, r);
}
function nuevoIdRed() {
  if (globalThis.crypto?.randomUUID) return crypto.randomUUID();
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === 'x' ? r : (r & 3) | 8).toString(16);
  });
}
const esperarRed = (ms) => new Promise((r) => setTimeout(r, ms));

async function llamarRed(funcion, cuerpo, keepalive) {
  const r = await fetch(`${RED.url}/rest/v1/rpc/${funcion}`, {
    method: 'POST',
    headers: { apikey: RED.clave, 'Content-Type': 'application/json' },
    body: JSON.stringify(cuerpo),
    keepalive: !!keepalive,
  });
  if (!r.ok) {
    const err = new Error(`red ${r.status}`);
    err.status = r.status;
    throw err;
  }
  const t = await r.text();
  return t ? JSON.parse(t) : null;
}

async function asegurarVisitaRed(forzar) {
  if (redRegistrada && !forzar) return;
  const red = leerRed();
  await llamarRed('registrar_visita', { p_cliente: red.id, p_apodo: red.apodo ?? 'Anónimo' });
  redRegistrada = true;
}

/** Envía las partidas pendientes, una a una (el servidor exige 10 s entre dos partidas del mismo jugador). */
async function vaciarColaRed() {
  if (redOcupada) return;
  redOcupada = true;
  try {
    if (!redActiva()) return;
    await asegurarVisitaRed();
    for (;;) {
      const cola = leerJSON(CLAVE_RED_COLA, []);
      if (!cola.length) break;
      try {
        await llamarRed('registrar_partida', cola[0]);
      } catch (err) {
        if (err.status !== 400) throw err; // sin conexión o servidor caído: se reintenta más tarde
        // 400: dato rechazado; se descarta para no bloquear la cola
      }
      const resto = leerJSON(CLAVE_RED_COLA, []).slice(1);
      guardarJSON(CLAVE_RED_COLA, resto);
      if (resto.length) await esperarRed(10500);
    }
  } catch (err) {
    /* sin conexión: queda en la cola */
  } finally {
    redOcupada = false;
  }
}

/** Al terminar una partida contra el ordenador, la pone en la cola y la envía. */
function enviarPartidaRed(e) {
  try {
    const red = leerRed();
    if (!redActiva() || ui.modo !== 'ordenador') return;
    const m = /^Ordenador \((.+)\)$/.exec(ui.nombres?.[ui.ladoOrdenador] ?? '');
    const nivel = m && NIVELES.find((n) => n.nombre.toLowerCase() === m[1]);
    if (!nivel) return;
    const yo = ui.abajo;
    const otro = RIVAL[yo];
    const secuencia = ui.secuencia ?? [];
    const g = golpesDeCronica({ secuencia, vidaInicial: ui.config.ajustes.vidaInicial }) ?? { blanco: 0, negro: 0 };
    const d = contarDobles({ secuencia });
    const dur = ui.inicioPartida ? Math.round((Date.now() - ui.inicioPartida) / 1000) : 0;
    const cola = leerJSON(CLAVE_RED_COLA, []);
    cola.push({
      p_cliente: red.id,
      p_nivel: nivel.id,
      p_gano: e.ganador === yo,
      p_dados: Math.min(g[yo], 200),
      p_recibidos: Math.min(g[otro], 200),
      p_dobles: Math.min(d.dobles, 100),
      p_subitas: Math.min(d.subitas, 50),
      p_duracion: Math.min(Math.max(dur, 0), 14400),
      p_version: RED.version,
    });
    guardarJSON(CLAVE_RED_COLA, cola.slice(-300));
    vaciarColaRed();
  } catch (err) {
    /* el ranking global nunca debe romper el juego */
  }
}

/** Mientras el juego está abierto y visible, avisa cada minuto (quién está conectado y cuánto tiempo). */
function iniciarLatidoRed() {
  if (latidoRed) return;
  const latir = () => {
    const red = leerRed();
    if (redActiva() && document.visibilityState === 'visible') llamarRed('latido', { p_cliente: red.id }).catch(() => {});
  };
  latidoRed = setInterval(latir, 60000);
  document.addEventListener('visibilitychange', latir);
}

// ---- Eventos de uso (qué funciones se usan y cómo se juega) ----
let eventosRed = [];
let eventosIniciados = false;

/** Anota un evento de uso; se envían en lotes. Solo si el jugador participa y ha aceptado el aviso actual. */
function eventoRed(tipo, dato) {
  try {
    if (!redActiva()) return;
    eventosRed.push({ t: tipo, d: dato ?? null, ts: Date.now() });
    if (eventosRed.length >= 40) volcarEventosRed();
  } catch (err) {
    /* nunca debe romper el juego */
  }
}

async function volcarEventosRed() {
  if (!eventosRed.length || !redActiva()) return;
  const lote = eventosRed.splice(0, 100);
  try {
    await asegurarVisitaRed();
    await llamarRed('registrar_eventos', { p_cliente: leerRed().id, p_eventos: lote }, true);
  } catch (err) {
    eventosRed = lote.concat(eventosRed).slice(-200); // se reintenta más tarde
  }
}

function iniciarEventosRed() {
  if (eventosIniciados) return;
  eventosIniciados = true;
  eventoRed('sesion', {
    ancho: innerWidth,
    alto: innerHeight,
    tactil: matchMedia('(pointer: coarse)').matches,
    pwa: matchMedia('(display-mode: standalone)').matches,
    idioma: navigator.language,
    oscuro: matchMedia('(prefers-color-scheme: dark)').matches,
    version: RED.version,
  });
  document.addEventListener('click', (ev) => {
    const b = ev.target.closest?.('[data-accion]');
    if (b) eventoRed('accion', { a: b.dataset.accion });
  }, true);
  setInterval(volcarEventosRed, 20000);
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') volcarEventosRed(); });
  addEventListener('pagehide', volcarEventosRed);
}

/** Estadísticas de una partida desde su crónica, vistas desde el jugador `yo` ('blanco' o 'negro'). */
function estadisticasPartidaRed(secuencia, yo) {
  const s = { series: 0, respuestas: 0, cartas: {}, cartasTotal: 0, rivalSeries: 0, rivalRespuestas: 0, pasosAtras: 0, paradas: 0, heridasDadas: 0, heridasRecibidas: 0 };
  for (const p of secuencia) {
    if (p.cartas) {
      if (p.jugador === yo) {
        if (p.contra) s.respuestas++; else s.series++;
        for (const c of p.cartas) { s.cartas[c] = (s.cartas[c] ?? 0) + 1; s.cartasTotal++; }
      } else if (p.contra) s.rivalRespuestas++; else s.rivalSeries++;
    } else if (p.tipo === 'pasoAtras' && p.jugador === yo) s.pasosAtras++;
    else if (p.tipo === 'puntoMuerto' && p.jugador === yo) s.paradas++;
    else if (p.tipo === 'herida') { if (p.atacante === yo) s.heridasDadas++; else s.heridasRecibidas++; }
  }
  return s;
}

/** Al terminar una partida (con el ordenador o entre dos personas). */
function eventoFinPartidaRed(e) {
  try {
    if (!redActiva()) return;
    const m = /^Ordenador \((.+)\)$/.exec(ui.nombres?.[ui.ladoOrdenador] ?? '');
    const nivel = ui.modo === 'ordenador' ? (m && NIVELES.find((n) => n.nombre.toLowerCase() === m[1])?.id) || null : null;
    const dur = ui.inicioPartida ? Math.round((Date.now() - ui.inicioPartida) / 1000) : null;
    eventoRed('partida_fin', { modo: ui.modo, nivel, gano: ui.modo === 'ordenador' ? e.ganador === ui.abajo : null, duracion: dur, ...estadisticasPartidaRed(ui.secuencia ?? [], ui.abajo) });
  } catch (err) {
    /* nunca debe romper el juego */
  }
}

/** Al participar (una sola vez), pone en la cola las partidas contra el ordenador ya guardadas en el Historial. */
function encolarHistoricoRed() {
  try {
    const red = leerRed();
    if (!redActiva() || red.historico) return;
    const cola = leerJSON(CLAVE_RED_COLA, []);
    const esOrd = (n) => /^Ordenador \(/.test(n ?? '');
    for (const p of leerPartidas()) {
      const lado = esOrd(p.negro) ? 'blanco' : esOrd(p.blanco) ? 'negro' : null;
      if (!lado) continue;
      const otro = lado === 'blanco' ? 'negro' : 'blanco';
      const m = /^Ordenador \((.+)\)$/.exec(p[otro]);
      const nivel = m && NIVELES.find((n) => n.nombre.toLowerCase() === m[1]);
      if (!nivel) continue; // niveles antiguos (normal, fácil): no se envían
      const g = p.golpes ?? { blanco: 0, negro: 0 };
      cola.push({
        p_cliente: red.id,
        p_nivel: nivel.id,
        p_gano: p.ganador === lado,
        p_dados: Math.min(g[lado] ?? 0, 200),
        p_recibidos: Math.min(g[otro] ?? 0, 200),
        p_dobles: Math.min(p.dobles ?? 0, 100),
        p_subitas: Math.min(p.subitas ?? 0, 50),
        p_duracion: 0,
        p_version: 'historico',
      });
    }
    guardarJSON(CLAVE_RED_COLA, cola.slice(-300));
    guardarRed({ ...red, historico: true });
  } catch (err) {
    /* sin almacenamiento: no se envía el histórico */
  }
}

/** Al arrancar: pregunta una sola vez si quiere participar; si participa, registra la visita. */
function iniciarRed() {
  const red = leerRed();
  if (!red.id) {
    red.id = nuevoIdRed();
    guardarRed(red);
  }
  if (red.participa === undefined || (red.participa && red.consentimiento !== CONSENTIMIENTO)) mostrarRed('consentimiento');
  else if (red.participa) {
    iniciarLatidoRed();
    iniciarEventosRed();
    encolarHistoricoRed();
    asegurarVisitaRed(true).then(vaciarColaRed).catch(() => {});
  }
}

function botonRed() {
  return '<p class="red-boton"><button class="secundario" data-accion="red-ranking">Ranking global</button></p>';
}

async function mostrarRed(modo) {
  const cont = $('#red-contenido');
  const dlg = $('#dlg-red');
  const red = leerRed();
  if (modo === 'consentimiento') {
    cont.innerHTML = `<h2>Ranking global</h2>
      <p>¿Quieres aparecer en el ranking global del juego y ayudarme con las pruebas?</p>
      <p class="red-aviso">Si participas, se recogen datos de uso del juego (tus partidas, las funciones que usas, el tiempo que juegas y el tipo de pantalla) junto a tu apodo y un identificador aleatorio. Nada personal. Puedes dejar de participar cuando quieras desde el ranking.</p>
      <label class="red-campo">Apodo <input id="red-apodo" maxlength="24" value="${escapar(red.apodo ?? leerNombres().yo ?? '')}" placeholder="Anónimo"></label>
      <div class="botones"><button class="principal" data-accion="red-si">Participar</button><button class="secundario" data-accion="red-no">No, gracias</button></div>`;
  } else {
    cont.innerHTML = '<h2>Ranking global</h2><p>Cargando…</p>';
    if (!dlg.open) dlg.showModal();
    let tabla;
    try {
      const filas = await llamarRed('ranking_global', {});
      tabla = filas?.length
        ? `<table class="tabla-ranking"><thead><tr><th>#</th><th>Apodo</th><th data-ayuda="Partidas contra el ordenador" tabindex="0">P</th><th data-ayuda="Partidas ganadas" tabindex="0">G</th><th data-ayuda="Puntos: cada victoria vale según el nivel vencido (Bisoño 1, Discípulo 2, Diestro 3, Preboste 4, Maestro 5)" tabindex="0">Puntos</th><th data-ayuda="Puntos de herida dados al rival" tabindex="0">Tocados</th></tr></thead><tbody>${filas
            .map((f, i) => `<tr><td>${i + 1}</td><td>${escapar(f.apodo)}</td><td>${f.partidas}</td><td>${f.ganadas}</td><td>${f.puntos}</td><td>${f.tocados}</td></tr>`)
            .join('')}</tbody></table>`
        : '<p>Todavía no hay partidas en el ranking.</p>';
    } catch (err) {
      tabla = '<p>No se ha podido cargar el ranking. Comprueba la conexión e inténtalo de nuevo.</p>';
    }
    const estado = red.participa ? `Participas como <b>${escapar(red.apodo ?? 'Anónimo')}</b>.` : 'No participas en el ranking.';
    cont.innerHTML = `<h2>Ranking global</h2>${tabla}<p class="nota-ranking">${estado}</p>
      <div class="botones"><button class="secundario" data-accion="red-cambiar">${red.participa ? 'Cambiar apodo' : 'Participar'}</button>${red.participa ? '<button class="secundario" data-accion="red-no">Dejar de participar</button>' : ''}<button class="principal" data-accion="red-cerrar">Cerrar</button></div>`;
    return;
  }
  if (!dlg.open) dlg.showModal();
}

function accionRed(a) {
  const dlg = $('#dlg-red');
  if (a === 'red-si') {
    const apodo = String($('#red-apodo')?.value ?? '').trim().slice(0, 24) || 'Anónimo';
    guardarRed({ ...leerRed(), participa: true, apodo, consentimiento: CONSENTIMIENTO });
    redRegistrada = false;
    dlg.close();
    iniciarLatidoRed();
    iniciarEventosRed();
    encolarHistoricoRed();
    asegurarVisitaRed(true).then(vaciarColaRed).catch(() => {});
  } else if (a === 'red-no') {
    guardarRed({ ...leerRed(), participa: false });
    guardarJSON(CLAVE_RED_COLA, []);
    dlg.close();
  } else if (a === 'red-cambiar') mostrarRed('consentimiento');
  else if (a === 'red-ranking') mostrarRed('ranking');
  else if (a === 'red-cerrar') dlg.close();
}


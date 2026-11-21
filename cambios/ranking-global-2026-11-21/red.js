// ---------- Ranking global (Supabase) ----------
// El juego envía, solo si el jugador lo acepta, el resultado de cada partida contra el ordenador.
// La clave "publishable" es pública por diseño: la seguridad está en la base de datos (solo se pueden
// llamar tres funciones, que validan lo que reciben; las tablas no se pueden leer ni escribir directamente).
const RED = {
  url: 'https://hbcalubchyzzxdjjgzzt.supabase.co',
  clave: 'sb_publishable_UKYAYdRbtw8sXVn4xvMsnw_NqT5WuYq',
  version: 'prueba-1',
};
const CLAVE_RED = 'destreza.red'; // { id, participa: true|false|undefined, apodo }
const CLAVE_RED_COLA = 'destreza.redCola'; // partidas pendientes de enviar (sin conexión)
let redRegistrada = false; // la visita (y el apodo) ya se han enviado en esta sesión
let redOcupada = false;
let latidoRed = null; // temporizador del pulso
let estrellasRed = 0; // estrellas elegidas en la ventana de opinión

function leerRed() {
  const r = leerJSON(CLAVE_RED, null);
  return r && typeof r === 'object' ? r : {};
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

async function llamarRed(funcion, cuerpo) {
  const r = await fetch(`${RED.url}/rest/v1/rpc/${funcion}`, {
    method: 'POST',
    headers: { apikey: RED.clave, 'Content-Type': 'application/json' },
    body: JSON.stringify(cuerpo),
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
    if (!leerRed().participa) return;
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
    if (!red.participa || ui.modo !== 'ordenador') return;
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
    if (red.participa && document.visibilityState === 'visible') llamarRed('latido', { p_cliente: red.id }).catch(() => {});
  };
  latidoRed = setInterval(latir, 60000);
  document.addEventListener('visibilitychange', latir);
}

/** Al participar (una sola vez), pone en la cola las partidas contra el ordenador ya guardadas en el Historial. */
function encolarHistoricoRed() {
  try {
    const red = leerRed();
    if (!red.participa || red.historico) return;
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
  if (red.participa === undefined) mostrarRed('consentimiento');
  else if (red.participa) {
    iniciarLatidoRed();
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
      <p class="red-aviso">Si participas, al terminar cada partida contra el ordenador se envían: tu apodo, el nivel del rival, si ganaste, los tocados, los dobles tocados, las muertes súbitas y lo que duró la partida, junto con un identificador aleatorio de este navegador. Nada más: ni correo ni datos personales. Puedes elegir un apodo y dejar de participar cuando quieras desde el ranking.</p>
      <label class="red-campo">Apodo <input id="red-apodo" maxlength="24" value="${escapar(red.apodo ?? leerNombres().yo ?? '')}" placeholder="Anónimo"></label>
      <div class="botones"><button class="principal" data-accion="red-si">Participar</button><button class="secundario" data-accion="red-no">No, gracias</button></div>`;
  } else if (modo === 'opinion') {
    estrellasRed = 0;
    cont.innerHTML = `<h2>Tu opinión</h2>
      <p>¿Qué te parece el juego?</p>
      <div class="red-estrellas">${[1, 2, 3, 4, 5].map((n) => `<button type="button" class="red-estrella" data-accion="red-estrella" data-n="${n}" aria-label="${n} ${n === 1 ? 'estrella' : 'estrellas'}">☆</button>`).join('')}</div>
      <label class="red-campo">Qué te ha gustado o qué cambiarías (opcional)<textarea id="red-texto" maxlength="500" rows="4"></textarea></label>
      <p id="red-aviso-op" class="red-aviso"></p>
      <div class="botones"><button class="principal" data-accion="red-enviar-opinion">Enviar</button><button class="secundario" data-accion="red-ranking">Volver</button></div>`;
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
      <div class="botones">${red.participa ? '<button class="secundario" data-accion="red-opinion">Dar mi opinión</button>' : ''}<button class="secundario" data-accion="red-cambiar">${red.participa ? 'Cambiar apodo' : 'Participar'}</button>${red.participa ? '<button class="secundario" data-accion="red-no">Dejar de participar</button>' : ''}<button class="principal" data-accion="red-cerrar">Cerrar</button></div>`;
    return;
  }
  if (!dlg.open) dlg.showModal();
}

function accionRed(a, boton) {
  const dlg = $('#dlg-red');
  if (a === 'red-si') {
    const apodo = String($('#red-apodo')?.value ?? '').trim().slice(0, 24) || 'Anónimo';
    guardarRed({ ...leerRed(), participa: true, apodo });
    redRegistrada = false;
    dlg.close();
    iniciarLatidoRed();
    encolarHistoricoRed();
    asegurarVisitaRed(true).then(vaciarColaRed).catch(() => {});
  } else if (a === 'red-no') {
    guardarRed({ ...leerRed(), participa: false });
    guardarJSON(CLAVE_RED_COLA, []);
    dlg.close();
  } else if (a === 'red-cambiar') mostrarRed('consentimiento');
  else if (a === 'red-ranking') mostrarRed('ranking');
  else if (a === 'red-opinion') mostrarRed('opinion');
  else if (a === 'red-estrella') {
    estrellasRed = Number(boton?.dataset.n) || 0;
    document.querySelectorAll('.red-estrella').forEach((b) => (b.textContent = Number(b.dataset.n) <= estrellasRed ? '★' : '☆'));
  } else if (a === 'red-enviar-opinion') {
    const aviso = $('#red-aviso-op');
    if (!estrellasRed) { aviso.textContent = 'Elige primero de 1 a 5 estrellas.'; return; }
    aviso.textContent = 'Enviando…';
    llamarRed('registrar_opinion', { p_cliente: leerRed().id, p_estrellas: estrellasRed, p_texto: $('#red-texto').value })
      .then(() => {
        $('#red-contenido').innerHTML = '<h2>¡Gracias!</h2><p>Tu opinión me ayuda mucho a mejorar el juego.</p><div class="botones"><button class="principal" data-accion="red-ranking">Volver al ranking</button></div>';
      })
      .catch(() => { aviso.textContent = 'No se ha podido enviar. Inténtalo de nuevo en un momento.'; });
  } else if (a === 'red-cerrar') dlg.close();
}


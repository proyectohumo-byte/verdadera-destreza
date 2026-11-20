# Aplica los parches A-D al index.html compilado (solo para reproducir la versión de prueba).
# Uso: python3 aplicar-parches.py index.html niveles.js salida.html
import sys
entrada, modulo, salida = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(entrada, encoding='utf-8').read()
niv = open(modulo, encoding='utf-8').read()
marca = '// ---- ui/datos.js ----'
assert s.count(marca) == 1
s = s.replace(marca, niv + marca)
viejo = '''        <label><input type="radio" name="nivel" value="reglas" checked> Normal: elige la mejor jugada según reglas fijas</label>
        <label><input type="radio" name="nivel" value="azar"> Fácil: juega cualquier jugada legal al azar</label>'''
assert s.count(viejo) == 1
nuevo = '''        <label><input type="radio" name="nivel" value="bisono"> <b>Bisoño</b>: Mozo recién llegado a la sala de armas: empuña la espada con respeto, pero poco sabe de ella.</label>
        <label><input type="radio" name="nivel" value="discipulo"> <b>Discípulo</b>: Aprende el compás bajo la vista del maestro: atiende a la estocada que tiene delante, no a la que vendrá.</label>
        <label><input type="radio" name="nivel" value="diestro" checked> <b>Diestro</b>: Hombre ya ducho en la ciencia de las armas: guarda memoria de tus últimas jugadas, aunque la memoria a veces le falla.</label>
        <label><input type="radio" name="nivel" value="preboste"> <b>Preboste</b>: Ayudante del maestro, con licencia para enseñar en su ausencia: lleva buena cuenta de las cartas, sin llegar a la certeza.</label>
        <label><input type="radio" name="nivel" value="maestro"> <b>Maestro</b>: Examinado en el arte y respetado en la plaza: casi nada se le escapa, pero ni ve tu mano ni es infalible.</label>'''
s = s.replace(viejo, nuevo)
v1 = "ui.rival = f.get('nivel') === 'azar' ? crearRivalAzar() : crearRivalReglas();"
assert s.count(v1) == 1
s = s.replace(v1, "ui.rival = crearRivalNivel(f.get('nivel'));")
v2 = "(f.get('nivel') === 'azar' ? 'Ordenador (fácil)' : 'Ordenador (normal)')"
assert s.count(v2) == 1
s = s.replace(v2, "`Ordenador (${nivelPorId(f.get('nivel')).nombre.toLowerCase()})`")
v3 = "  ui.rival = crearRivalReglas();\n  $('#defs')"
assert s.count(v3) == 1
s = s.replace(v3, "  ui.rival = crearRivalNivel(NIVEL_POR_DEFECTO);\n  $('#defs')")
v5 = "const primera = ci === 0 && esDeclarada ? `<span class=\"suma-serie\">suma ${danoPendiente(e).suma}</span>` : '';"
assert s.count(v5) == 1
n5 = "const dp = danoPendiente(e);\n        const primera = ci === 0 && esDeclarada ? `<span class=\"suma-serie\" title=\"${dp.suma} de la serie${dp.mas1 ? ' + 1 por contestar una carta del rival' : ' (sin +1: abre el combate)'}${dp.extra ? ' + ' + dp.extra + ' por la apertura cercana rival' : ''}\">suma ${dp.dano}</span>` : '';"
s = s.replace(v5, n5)
v6 = "function render() {\n  const e = ui.pausa ? ui.pausa.estado : ui.estado;"
assert s.count(v6) == 1
n6 = r'''// ---------- Partida en curso: se guarda en este dispositivo y se retoma al recargar ----------

const CLAVE_EN_CURSO = 'destreza.enCurso';

function guardarEnCurso() {
  try {
    if (!ui.ajustesPartida || !ui.estado) return; // aún no se ha empezado ninguna partida
    if (ui.estado.fase === 'fin') {
      localStorage.removeItem(CLAVE_EN_CURSO); // la partida terminada ya está en el Historial
      return;
    }
    const sinConfig = (e) => ({ ...e, config: undefined });
    localStorage.setItem(CLAVE_EN_CURSO, JSON.stringify({
      v: 1,
      modo: ui.modo,
      abajo: ui.abajo,
      ladoOrdenador: ui.ladoOrdenador,
      nivel: ui.rival?.nivel ?? null,
      nombres: ui.nombres,
      ajustes: ui.ajustesPartida,
      estado: sinConfig(ui.estado),
      pausa: ui.pausa ? { ...ui.pausa, estado: sinConfig(ui.pausa.estado) } : null,
      registro: ui.registro,
      manoVisible: ui.manoVisible,
    }));
  } catch (err) { /* sin almacenamiento: la partida sigue, solo que no se podrá retomar */ }
}

/** Si hay una partida guardada la restaura y devuelve true; si algo falla, la descarta y devuelve false. */
function retomarEnCurso() {
  try {
    const g = JSON.parse(localStorage.getItem(CLAVE_EN_CURSO));
    if (!g || g.v !== 1 || !g.estado || g.estado.fase === 'fin') return false;
    const config = crearConfig(ui.datos.cartas, g.ajustes);
    ui.config = config;
    ui.ajustesPartida = g.ajustes;
    ui.modo = g.modo;
    ui.abajo = g.abajo;
    ui.ladoOrdenador = g.ladoOrdenador;
    ui.rival = crearRivalNivel(g.nivel);
    ui.nombres = g.nombres;
    ui.estado = { ...g.estado, config };
    ui.pausa = g.pausa ? { ...g.pausa, estado: { ...g.pausa.estado, config } } : null;
    ui.registro = [...(g.registro ?? []), { texto: 'Partida retomada tras recargar la página.', tipo: 'inicio' }];
    ui.secuencia = [];
    ui.pensando = false;
    ui.manoVisible = !!g.manoVisible;
    limpiarSeleccion();
    ui.mensaje = null;
    $('#defs').innerHTML = defsSvg(config.cartas);
    render();
    return true;
  } catch (err) {
    try { localStorage.removeItem(CLAVE_EN_CURSO); } catch (e2) { /* nada */ }
    // Deja el juego como al arrancar, por si la restauración falló a medias.
    ui.config = crearConfig(ui.datos.cartas, ui.datos.ajustes);
    ui.estado = nuevaPartida(ui.config);
    ui.ajustesPartida = undefined;
    ui.pausa = null;
    ui.registro = [];
    ui.modo = 'ordenador';
    ui.abajo = 'blanco';
    ui.ladoOrdenador = 'negro';
    ui.nombres = undefined;
    ui.rival = crearRivalNivel(NIVEL_POR_DEFECTO);
    return false;
  }
}

function render() {
  guardarEnCurso();
  const e = ui.pausa ? ui.pausa.estado : ui.estado;'''
s = s.replace(v6, n6)
v7 = "  ui.config = crearConfig(ui.datos.cartas, ajustes);\n  ui.estado = nuevaPartida(ui.config);\n  ui.registro = [{ texto: `Nueva partida."
assert s.count(v7) == 1
s = s.replace(v7, "  ui.config = crearConfig(ui.datos.cartas, ajustes);\n  ui.ajustesPartida = ajustes;\n  ui.estado = nuevaPartida(ui.config);\n  ui.registro = [{ texto: `Nueva partida.")
v8 = "  $('#reglas-contenido').innerHTML = htmlComoJugar(ui.config);\n  render();\n  abrirNuevaPartida();"
assert s.count(v8) == 1
s = s.replace(v8, "  $('#reglas-contenido').innerHTML = htmlComoJugar(ui.config);\n  if (retomarEnCurso()) return;\n  render();\n  abrirNuevaPartida();")

v9 = '<th>#</th><th>Esgrimista</th><th title="Partidas">P</th><th title="Ganadas">G</th><th title="Empates">E</th><th title="Perdidas">Pe</th><th title="Porcentaje de victorias">%</th><th title="Puntos de herida dados / recibidos">Tocados</th>'
assert s.count(v9) == 1
n9 = '<th data-ayuda="Posición en la clasificación" tabindex="0">#</th><th>Esgrimista</th><th data-ayuda="Partidas jugadas" tabindex="0">P</th><th data-ayuda="Partidas ganadas" tabindex="0">G</th><th data-ayuda="Partidas empatadas" tabindex="0">E</th><th data-ayuda="Partidas perdidas" tabindex="0">Pe</th><th data-ayuda="Porcentaje de partidas ganadas" tabindex="0">%</th><th data-ayuda="Puntos de herida dados / recibidos" tabindex="0">Tocados</th>'
s = s.replace(v9, n9)
v10 = ".tabla-ranking tbody tr:first-child td { font-weight: bold; }"
assert s.count(v10) == 1
n10 = v10 + """
.tabla-ranking th[data-ayuda] { position: relative; cursor: help; text-decoration: underline dotted; text-underline-offset: 3px; }
.tabla-ranking th[data-ayuda]:hover::after, .tabla-ranking th[data-ayuda]:focus::after {
  content: attr(data-ayuda); position: absolute; top: 100%; left: 50%; transform: translateX(-50%); z-index: 5;
  background: #2b1d12; color: #f7ecd6; font-size: 12px; font-weight: normal; line-height: 1.3; white-space: nowrap;
  padding: 4px 8px; border-radius: 4px; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4); text-decoration: none; pointer-events: none;
}
.tabla-ranking th[data-ayuda]:nth-last-child(-n+2):hover::after, .tabla-ranking th[data-ayuda]:nth-last-child(-n+2):focus::after { left: auto; right: 0; transform: none; }
.tabla-ranking th[data-ayuda]:first-child:hover::after, .tabla-ranking th[data-ayuda]:first-child:focus::after { left: 0; transform: none; }"""
s = s.replace(v10, n10)

v11 = "function abrirRanking() {\n  const todas = leerPartidas();"
assert s.count(v11) == 1
n11 = r'''/** Resultados de cada esgrimista contra cada rival concreto (por ejemplo, "Ordenador (diestro)"). */
function htmlEnfrentamientos(partidas) {
  const orden = ['bisoño', 'discípulo', 'diestro', 'preboste', 'maestro'];
  const peso = (nombre) => {
    const m = /^Ordenador \((.+)\)$/.exec(nombre);
    return m ? orden.indexOf(m[1].toLowerCase()) : -1;
  };
  const filas = new Map();
  for (const p of partidas) {
    for (const lado of ['blanco', 'negro']) {
      const otro = lado === 'blanco' ? 'negro' : 'blanco';
      if (/^Ordenador/.test(p[lado])) continue; // el ordenador no necesita su propia fila
      const k = `${p[lado]}\u0000${p[otro]}`;
      if (!filas.has(k)) filas.set(k, { yo: p[lado], rival: p[otro], jugadas: 0, ganadas: 0, empates: 0, perdidas: 0, dados: 0, recibidos: 0 });
      const f = filas.get(k);
      f.jugadas++;
      if (p.ganador === lado) f.ganadas++;
      else if (p.ganador === null) f.empates++;
      else f.perdidas++;
      if (p.vida && p.vidaInicial) {
        f.dados += p.vidaInicial - p.vida[otro];
        f.recibidos += p.vidaInicial - p.vida[lado];
      }
    }
  }
  const lista = [...filas.values()].sort((a, b) => a.yo.localeCompare(b.yo, 'es') || peso(a.rival) - peso(b.rival) || a.rival.localeCompare(b.rival, 'es'));
  if (!lista.length) return '';
  const cab = (t, ayuda) => `<th data-ayuda="${ayuda}" tabindex="0">${t}</th>`;
  const cuerpo = lista
    .map((f) => `<tr><td>${escapar(f.yo)} contra ${escapar(f.rival)}</td><td>${f.jugadas}</td><td>${f.ganadas}</td><td>${f.empates}</td><td>${f.perdidas}</td><td>${Math.round((100 * f.ganadas) / f.jugadas)}</td><td>${f.dados} / ${f.recibidos}</td></tr>`)
    .join('');
  return `<details class="bloque-ranking" open><summary>Resultados contra cada rival</summary><table class="tabla-ranking"><thead><tr><th>Enfrentamiento</th>${cab('P', 'Partidas jugadas')}${cab('G', 'Partidas ganadas')}${cab('E', 'Partidas empatadas')}${cab('Pe', 'Partidas perdidas')}${cab('%', 'Porcentaje de partidas ganadas')}${cab('Tocados', 'Puntos de herida dados / recibidos')}</tr></thead><tbody>${cuerpo}</tbody></table></details>`;
}

function abrirRanking() {
  const todas = leerPartidas();'''
s = s.replace(v11, n11)
v12 = "$('#ranking-contenido').innerHTML = filtros + partidas + ranking;"
assert s.count(v12) == 1
s = s.replace(v12, "$('#ranking-contenido').innerHTML = htmlEnfrentamientos(todas) + ranking + filtros + partidas;")

v13 = "dialog::backdrop { background: #1f1711b3; }"
assert s.count(v13) == 1
s = s.replace(v13, v13 + """
.cerrar-x { position: sticky; top: 0; float: right; z-index: 4; width: 34px; height: 34px; margin: -10px -14px 0 8px; padding: 0; display: flex; align-items: center; justify-content: center; font-size: 26px; line-height: 1; color: var(--tinta); background: transparent; border: 1px solid transparent; border-radius: 50%; cursor: pointer; }
.cerrar-x:hover, .cerrar-x:focus-visible { background: var(--papel-claro); border-color: var(--tinta-suave); color: var(--sangre); }""")
v14 = "  enlazarEventos();\n  enlazarArrastre();"
assert s.count(v14) == 1
s = s.replace(v14, """  // Una cruz arriba a la derecha en cada ventana emergente (Nueva partida, Historial, Cómo jugar).
  for (const d of document.querySelectorAll('dialog')) {
    const x = document.createElement('button');
    x.type = 'button';
    x.className = 'cerrar-x';
    x.textContent = '×';
    x.title = 'Cerrar';
    x.setAttribute('aria-label', 'Cerrar');
    x.addEventListener('click', () => d.close());
    d.prepend(x);
  }
""" + v14)

v15 = "function calcularRanking(partidas) {"
assert s.count(v15) == 1
s = s.replace(v15, r'''/**
 * Puntos de herida dados por cada color según la crónica de la partida. Cuenta también los puntos
 * perdidos antes de una muerte súbita (los dos vuelven a 1), que "vida inicial - vida final" no ve.
 * Devuelve null si la partida no tiene crónica. Se calcula UNA vez, al terminar la partida, y se guarda en
 * la propia partida (`golpes`); el ranking solo suma lo guardado.
 */
function golpesDeCronica(p) {
  if (!p.secuencia?.length || !p.vidaInicial) return null;
  const v = { blanco: p.vidaInicial, negro: p.vidaInicial };
  const dados = { blanco: 0, negro: 0 };
  for (const paso of p.secuencia) {
    if (paso.tipo === 'herida') {
      dados[paso.atacante] += Math.max(0, v[paso.herido] - paso.vida);
      v[paso.herido] = paso.vida;
    } else if (paso.tipo === 'doble') {
      const subita = /súbita/.test(paso.resultado ?? '');
      for (const j of ['blanco', 'negro']) {
        dados[j === 'blanco' ? 'negro' : 'blanco'] += subita ? v[j] : Math.max(0, v[j] - paso.vida[j]);
        v[j] = paso.vida[j];
      }
    }
  }
  return dados;
}

function calcularRanking(partidas) {''')
v18 = "      if (p.vida && p.vidaInicial) {\n        f.puntosDados += p.vidaInicial - p.vida[otro];"
assert s.count(v18) == 1
s = s.replace(v18, "      if (p.golpes) {\n        f.puntosDados += p.golpes[lado];\n        f.puntosRecibidos += p.golpes[otro];\n      } else if (p.vida && p.vidaInicial) {\n        f.puntosDados += p.vidaInicial - p.vida[otro];")
v19 = "      if (p.vida && p.vidaInicial) {\n        f.dados += p.vidaInicial - p.vida[otro];"
assert s.count(v19) == 1
s = s.replace(v19, "      if (p.golpes) {\n        f.dados += p.golpes[lado];\n        f.recibidos += p.golpes[otro];\n      } else if (p.vida && p.vidaInicial) {\n        f.dados += p.vidaInicial - p.vida[otro];")
# partida en curso: la crónica también se guarda y se restaura
v21 = "      registro: ui.registro,\n      manoVisible: ui.manoVisible,"
assert s.count(v21) == 1
s = s.replace(v21, "      registro: ui.registro,\n      secuencia: ui.secuencia ?? [],\n      manoVisible: ui.manoVisible,")
v22 = "    ui.secuencia = [];\n    ui.pensando = false;\n    ui.manoVisible = !!g.manoVisible;"
assert s.count(v22) == 1
s = s.replace(v22, "    ui.secuencia = g.secuencia ?? [];\n    ui.pensando = false;\n    ui.manoVisible = !!g.manoVisible;")

v23 = "    vidaInicial: ui.config.ajustes.vidaInicial,\n    secuencia: ui.secuencia ?? [],"
assert s.count(v23) == 1
s = s.replace(v23, "    vidaInicial: ui.config.ajustes.vidaInicial,\n    golpes: golpesDeCronica({ secuencia: ui.secuencia ?? [], vidaInicial: ui.config.ajustes.vidaInicial }) ?? undefined,\n    secuencia: ui.secuencia ?? [],")
v24 = "let filtroHistorial = 'todas';"
assert s.count(v24) == 1
s = s.replace(v24, r'''// PARCHE TEMPORAL (solo para la versión de prueba; NO llevar a la versión final).
// Las partidas guardadas antes de este cambio no tienen `golpes`: se calculan una sola vez desde su
// crónica y se guardan, de modo que quedan fijas como las demás. En la versión final todas las partidas
// ya se registran con `golpes`, así que esta función sobra y debe borrarse (con su llamada en `iniciar`).
function migrarGolpesPartidasAntiguas() {
  try {
    const todas = leerPartidas();
    let cambios = 0;
    for (const p of todas) {
      if (p.golpes) continue;
      const g = golpesDeCronica(p);
      if (g) { p.golpes = g; cambios++; }
    }
    if (cambios) guardarJSON(CLAVE_PARTIDAS, todas);
  } catch (err) { /* sin almacenamiento: se queda el cálculo antiguo */ }
}

let filtroHistorial = 'todas';''')
v25 = "  enlazarEventos();\n  enlazarArrastre();"
assert s.count(v25) == 1
s = s.replace(v25, "  migrarGolpesPartidasAntiguas(); // PARCHE TEMPORAL: borrar en la versión final\n" + v25)

# Columnas DT (dobles tocados) y MS (muertes súbitas) en lugar de E (empates): no se puede empatar.
def _una(viejo, nuevo, veces=1):
    global s
    assert s.count(viejo) == veces, (veces, s.count(viejo), viejo[:60])
    s = s.replace(viejo, nuevo)
_una("{ nombre, jugadas: 0, ganadas: 0, empates: 0, perdidas: 0, puntosDados: 0, puntosRecibidos: 0 }", "{ nombre, jugadas: 0, ganadas: 0, empates: 0, perdidas: 0, dobles: 0, subitas: 0, puntosDados: 0, puntosRecibidos: 0 }")
_una("{ yo: p[lado], rival: p[otro], jugadas: 0, ganadas: 0, empates: 0, perdidas: 0, dados: 0, recibidos: 0 }", "{ yo: p[lado], rival: p[otro], jugadas: 0, ganadas: 0, empates: 0, perdidas: 0, dobles: 0, subitas: 0, dados: 0, recibidos: 0 }")
_una("      f.jugadas++;\n", "      f.jugadas++;\n      f.dobles += p.dobles ?? 0;\n      f.subitas += p.subitas ?? 0;\n", 2)
_una("<td>${f.ganadas}</td><td>${f.empates}</td><td>${f.perdidas}</td>", "<td>${f.ganadas}</td><td>${f.perdidas}</td><td>${f.dobles}</td><td>${f.subitas}</td>", 2)
_una("""<th data-ayuda="Partidas empatadas" tabindex="0">E</th><th data-ayuda="Partidas perdidas" tabindex="0">Pe</th>""", """<th data-ayuda="Partidas perdidas" tabindex="0">Pe</th><th data-ayuda="Dobles tocados (Estocada contra Estocada), incluidas las muertes súbitas" tabindex="0">DT</th><th data-ayuda="Muertes súbitas: los dos a 0 a la vez y vuelven a 1" tabindex="0">MS</th>""")
_una("${cab('E', 'Partidas empatadas')}${cab('Pe', 'Partidas perdidas')}", "${cab('Pe', 'Partidas perdidas')}${cab('DT', 'Dobles tocados (Estocada contra Estocada), incluidas las muertes súbitas')}${cab('MS', 'Muertes súbitas: los dos a 0 a la vez y vuelven a 1')}")
# Se cuentan una sola vez, al terminar la partida, desde la crónica.
_una("function calcularRanking(partidas) {", """/** Dobles tocados y muertes súbitas de una partida, según su crónica. */
function contarDobles(p) {
  const dobles = (p.secuencia ?? []).filter((x) => x.tipo === 'doble');
  return { dobles: dobles.length, subitas: dobles.filter((x) => /súbita/.test(x.resultado ?? '')).length };
}

function calcularRanking(partidas) {""")
_una("    golpes: golpesDeCronica({ secuencia: ui.secuencia ?? [], vidaInicial: ui.config.ajustes.vidaInicial }) ?? undefined,\n", "    golpes: golpesDeCronica({ secuencia: ui.secuencia ?? [], vidaInicial: ui.config.ajustes.vidaInicial }) ?? undefined,\n    ...contarDobles({ secuencia: ui.secuencia ?? [] }),\n")
_una("      if (p.golpes) continue;\n      const g = golpesDeCronica(p);\n      if (g) { p.golpes = g; cambios++; }", "      if (p.dobles === undefined && p.secuencia?.length) { Object.assign(p, contarDobles(p)); cambios++; }\n      if (p.golpes) continue;\n      const g = golpesDeCronica(p);\n      if (g) { p.golpes = g; cambios++; }")

v30 = "/** Resultados de cada esgrimista contra cada rival concreto (por ejemplo, \"Ordenador (diestro)\"). */"
assert s.count(v30) == 1
s = s.replace(v30, r'''/**
 * Título del jugador según su fuerza, estimada con las partidas guardadas contra el ordenador. Cada nivel
 * del ordenador tiene una fuerza fija (NIVELES[].fuerza, escala tipo Elo). Se busca la fuerza que mejor
 * explica los resultados (con una expectativa previa prudente) y se toma un valor pesimista (percentil 20),
 * de modo que pocas partidas no den un título alto. Además, no se sube más de 120 puntos por encima del
 * rival más fuerte al que se ha retado con cierta regularidad (3 partidas): ganar cien veces a Bisoño no
 * hace Maestro. Ni cuenta el número de partidas ni basta una racha contra un solo nivel.
 */
const TITULO = { previa: 0, desviacionPrevia: 200, percentil: 0.2, techoSobreRival: 120, minimoPartidas: 5, minimoPorNivel: 3, coste: [6, 9, 12, 15, 18], dominioRatio: 0.55 };

function fuerzaDeRival(nombre) {
  const m = /^Ordenador \((.+)\)$/.exec(nombre);
  if (!m) return null;
  const clave = m[1].toLowerCase();
  const nivel = NIVELES.find((n) => n.nombre.toLowerCase() === clave);
  if (nivel) return nivel.fuerza;
  return FUERZA_RIVAL_ANTIGUO[clave] ?? null;
}

function tituloEsgrimista(nombre, partidas) {
  const juegos = [];
  for (const p of partidas) {
    for (const lado of ['blanco', 'negro']) {
      if (p[lado] !== nombre) continue;
      const f = fuerzaDeRival(p[lado === 'blanco' ? 'negro' : 'blanco']);
      if (f === null) continue;
      juegos.push({ f, res: p.ganador === null ? 0.5 : p.ganador === lado ? 1 : 0 });
    }
  }
  if (juegos.length < TITULO.minimoPartidas) {
    return { titulo: null, partidas: juegos.length, fuerza: null, siguiente: NIVELES[0].nombre, falta: `juega ${TITULO.minimoPartidas - juegos.length} ${TITULO.minimoPartidas - juegos.length === 1 ? 'partida más' : 'partidas más'} contra el ordenador` };
  }
  const esperado = (R, Ro) => 1 / (1 + Math.pow(10, (Ro - R) / 400));
  const rejilla = [];
  let max = -Infinity;
  for (let R = -400; R <= 800; R += 5) {
    let lp = -((R - TITULO.previa) ** 2) / (2 * TITULO.desviacionPrevia ** 2);
    for (const g of juegos) { const e = esperado(R, g.f); lp += g.res * Math.log(e) + (1 - g.res) * Math.log(1 - e); }
    rejilla.push([R, lp]);
    if (lp > max) max = lp;
  }
  const pesos = rejilla.map(([R, lp]) => [R, Math.exp(lp - max)]);
  const total = pesos.reduce((a, [, w]) => a + w, 0);
  const media = pesos.reduce((a, [R, w]) => a + R * w, 0) / total;
  let acum = 0;
  let pesimista = pesos[pesos.length - 1][0];
  for (const [R, w] of pesos) { acum += w / total; if (acum >= TITULO.percentil) { pesimista = R; break; } }
  const porNivel = new Map();
  for (const g of juegos) porNivel.set(g.f, (porNivel.get(g.f) ?? 0) + 1);
  const retados = [...porNivel].filter(([, n]) => n >= TITULO.minimoPorNivel).map(([f]) => f);
  const techo = retados.length ? Math.max(...retados) + TITULO.techoSobreRival : -Infinity;
  const fuerza = Math.min(pesimista, techo);
  const alcanzados = NIVELES.filter((n) => n.fuerza <= fuerza);
  // Cada categoría se gana venciendo a su propio nivel con cierta soltura, y en orden: no se llega a
  // Maestro sin haber dominado antes Bisoño, Discípulo, Diestro y Preboste.
  const marcador = new Map();
  for (const p of partidas) {
    for (const lado of ['blanco', 'negro']) {
      if (p[lado] !== nombre) continue;
      const m = /^Ordenador \((.+)\)$/.exec(p[lado === 'blanco' ? 'negro' : 'blanco']);
      if (!m) continue;
      const clave = m[1].toLowerCase() === 'normal' ? 'maestro' : m[1].toLowerCase();
      const n = NIVELES.find((x) => x.nombre.toLowerCase() === clave);
      if (!n) continue;
      const st = marcador.get(n.id) ?? { n: 0, g: 0 };
      st.n++;
      if (p.ganador === lado) st.g++;
      marcador.set(n.id, st);
    }
  }
  const dom = NIVELES.map((n, k) => {
    const st = marcador.get(n.id) ?? { n: 0, g: 0 };
    return st.n >= TITULO.coste[k] && st.g / st.n >= TITULO.dominioRatio;
  });
  // Cuánto queda en cada categoría: partidas que faltan y victorias necesarias para llegar al porcentaje.
  const progreso = NIVELES.map((n, k) => {
    const st = marcador.get(n.id) ?? { n: 0, g: 0 };
    let m = Math.max(0, TITULO.coste[k] - st.n);
    let w = 0;
    for (; m <= 500; m++) {
      w = Math.max(0, Math.ceil(TITULO.dominioRatio * (st.n + m) - 1e-9) - st.g);
      if (w <= m) break;
    }
    return { nombre: n.nombre, n: st.n, g: st.g, dominado: dom[k], partidas: m, victorias: w, coste: TITULO.coste[k] };
  });
  let enOrden = 0; // niveles dominados seguidos desde Bisoño
  while (enOrden < dom.length && dom[enOrden]) enOrden++;
  const masAlto = dom.lastIndexOf(true); // nivel más fuerte dominado (-1 si ninguno)
  let falta = null;
  const sinDominar = NIVELES[enOrden];
  if (sinDominar) {
    const st = marcador.get(sinDominar.id) ?? { n: 0, g: 0 };
    const resto = TITULO.coste[enOrden] - st.n;
    falta = resto > 0
      ? `juega ${resto} ${resto === 1 ? 'partida más' : 'partidas más'} contra ${sinDominar.nombre}`
      : `gana con más soltura a ${sinDominar.nombre} (llevas ${Math.round((100 * st.g) / st.n)} %, hacen falta ${Math.round(100 * TITULO.dominioRatio)} %)`;
  }
  // Dominar un nivel te pasa a la categoría siguiente (vencer a Bisoño te hace Discípulo), y no más. Cada
  // escalón cuesta más que el anterior (TITULO.coste: 6, 9, 12, 15 partidas con soltura). Ir directo a un nivel
  // fuerte, saltándose los anteriores, también da crédito, pero compensa pasar por todas las categorías: se
  // exige el coste de TODOS los escalones saltados (más el del propio nivel) y ganando contra el nivel fuerte, que
  // es más difícil. El crédito llega solo hasta UNA categoría por debajo del nivel vencido (una cantidad
  // grande de victorias contra Preboste da Diestro; contra Diestro, Discípulo; contra Maestro, Preboste).
  // Maestro exige haber combatido con soltura contra todos los niveles anteriores.
  const ultimo = NIVELES.length - 1;
  let credito = -1;
  NIVELES.forEach((n, j) => {
    const saltados = dom.slice(0, j).filter((d) => !d).length;
    if (!saltados) return;
    const st = marcador.get(n.id) ?? { n: 0, g: 0 };
    // Se exige el coste de todos los escalones que se saltan, más el del propio nivel, ganando contra ese nivel fuerte.
    const exigidas = NIVELES.reduce((a, _, i) => a + (i < j && !dom[i] ? TITULO.coste[i] : 0), TITULO.coste[j]);
    if (st.n >= exigidas && st.g / st.n >= TITULO.dominioRatio) credito = Math.max(credito, j - 1);
  });
  const porRecorrido = enOrden >= ultimo ? ultimo : Math.min(Math.max(enOrden, credito), ultimo - 1);
  const porFuerza = Math.max(alcanzados.length - 1, 0);
  const indice = Math.min(porRecorrido, porFuerza);
  const nivel = NIVELES[indice];
  const siguiente = NIVELES[indice + 1] ?? null;
  if (siguiente && porFuerza < porRecorrido) falta = 'sigue ganando a rivales fuertes: tu nivel de juego aún no alcanza al suyo';
  else if (siguiente && indice + 1 === ultimo && enOrden < ultimo) falta = `para ser ${siguiente.nombre} tienes que combatir con todos los niveles: ${falta}`;
  return { titulo: nivel?.nombre ?? null, partidas: juegos.length, fuerza: Math.round(media), siguiente: siguiente?.nombre ?? null, falta, progreso };
}

function htmlTitulos(partidas) {
  const nombres = [...new Set(partidas.flatMap((p) => [p.blanco, p.negro]))].filter((n) => !/^Ordenador/.test(n));
  const filas = nombres
    .map((n) => ({ n, t: tituloEsgrimista(n, partidas) }))
    .filter((x) => x.t.partidas > 0)
    .map(({ n, t }) => {
      const texto = t.titulo
        ? `<strong>${escapar(t.titulo)}</strong>`
        : `<em>Sin título aún</em>`;
      const nota = t.siguiente ? `Para ser ${t.siguiente}: ${t.falta}.` : 'Es el título más alto.';
      const progreso = t.progreso
        ? `<ul class="progreso-titulo">${t.progreso
            .map((x) => {
              const pct = x.n ? Math.round((100 * x.g) / x.n) : 0;
              const resto = `te ${x.partidas === 1 ? 'queda' : 'quedan'} ${x.partidas} ${x.partidas === 1 ? 'partida' : 'partidas'}, ganando al menos ${x.victorias}`;
              return `<li class="${x.dominado ? 'hecho' : ''}">${x.dominado ? '✓' : '·'} ${escapar(x.nombre)}: ${x.dominado ? `dominado (${x.g} de ${x.n}, ${pct} %)` : `${x.n} de ${x.coste} partidas${x.n ? `, ${pct} %` : ''}: ${resto}`}</li>`;
            })
            .join('')}</ul>`
        : '';
      return `<li title="${escapar(nota)}"><span class="titulo-nombre">${escapar(n)}</span> ${texto} <span class="titulo-detalle">(${t.partidas} ${t.partidas === 1 ? 'partida' : 'partidas'} contra el ordenador)</span>${progreso}</li>`;
    });
  if (!filas.length) return '';
  return `<div class="bloque-titulos"><h3>Título de esgrimista</h3><ul>${filas.join('')}</ul><p class="nota-titulo">Cada categoría se gana venciendo a su propio nivel con soltura, y en orden. Saltarte niveles cuesta mucho más. Mide cómo juegas, no cuántas partidas llevas.</p></div>`;
}

/** Resultados de cada esgrimista contra cada rival concreto (por ejemplo, "Ordenador (diestro)"). */''')
v31 = "$('#ranking-contenido').innerHTML = htmlEnfrentamientos(todas) + ranking + filtros + partidas;"
assert s.count(v31) == 1
s = s.replace(v31, "$('#ranking-contenido').innerHTML = htmlTitulos(todas) + htmlEnfrentamientos(todas) + ranking + filtros + partidas;")
v32 = ".tabla-ranking { width: 100%; border-collapse: collapse; font-size: 14px; }"
assert s.count(v32) == 1
s = s.replace(v32, """.bloque-titulos { margin: 4px 0 12px; padding: 8px 12px; border: 1px solid var(--tinta-suave); border-radius: 2px; background: rgba(255, 255, 255, 0.35); }
.bloque-titulos h3 { margin: 0 0 4px; font-size: 15px; }
.bloque-titulos ul { list-style: none; margin: 0; padding: 0; }
.bloque-titulos li { padding: 2px 0; cursor: help; }
.bloque-titulos .titulo-nombre { font-weight: bold; margin-right: 6px; }
.bloque-titulos strong { color: var(--sangre); }
.bloque-titulos .titulo-detalle, .bloque-titulos .nota-titulo { font-size: 12px; opacity: 0.75; }
.bloque-titulos .nota-titulo { margin: 4px 0 0; font-style: italic; }
.progreso-titulo { list-style: none; margin: 4px 0 2px; padding: 0; font-size: 12.5px; }
.progreso-titulo li { padding: 1px 0; opacity: 0.85; }
.progreso-titulo li.hecho { opacity: 1; color: var(--sangre); }
""" + v32)

open(salida, 'w', encoding='utf-8').write(s)
print('ok', len(s))

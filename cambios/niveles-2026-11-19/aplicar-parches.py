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

open(salida, 'w', encoding='utf-8').write(s)
print('ok', len(s))

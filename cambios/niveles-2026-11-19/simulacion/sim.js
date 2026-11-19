// Simulador: enfrenta rivales entre sí en el motor del juego (sin navegador).
const { cargar } = require('./harness.js');

function mulberry(a) {
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function jugarPartida(M, datos, rivales, opts = {}) {
  const rng = mulberry(opts.semilla ?? 1);
  const ajustes = { ...datos.ajustes, circuloBlancoExtra: datos.ajustes.circuloBlancoExtra ?? [], abrenCombateExtra: datos.ajustes.abrenCombateExtra ?? [], primeroEnDeclarar: opts.primero ?? 'aleatorio', tamanoMano: opts.mano === 'todas' ? null : 5 };
  const config = M.crearConfig(datos.cartas, ajustes);
  let e = M.nuevaPartida(config, { rng });
  let pasos = 0;
  while (e.fase !== 'fin' && pasos < 2000) {
    const jug = rivales[e.turno].elegir(e, rng);
    e = M.aplicar(e, jug);
    pasos++;
  }
  return { ganador: e.fase === 'fin' ? (e.empate ? 'empate' : e.ganador) : 'colgada', pasos, series: e.contadores.series, heridas: e.contadores.heridas };
}

// Enfrenta A contra B n partidas alternando colores. Devuelve % de victorias de A.
function duelo(M, datos, crearA, crearB, n, semilla0 = 100, opts = {}) {
  let a = 0, b = 0, otros = 0, pasos = 0;
  for (let i = 0; i < n; i++) {
    const colorA = i % 2 === 0 ? 'blanco' : 'negro';
    const rivales = { [colorA]: crearA(), [colorA === 'blanco' ? 'negro' : 'blanco']: crearB() };
    const r = jugarPartida(M, datos, rivales, { semilla: semilla0 + i, primero: i % 4 < 2 ? 'blanco' : 'negro', ...opts });
    pasos += r.pasos;
    if (r.ganador === colorA) a++; else if (r.ganador === 'blanco' || r.ganador === 'negro') b++; else otros++;
  }
  return { a, b, otros, pctA: a / (a + b || 1), pasosMedios: pasos / n };
}
module.exports = { jugarPartida, duelo, mulberry };

if (require.main === module) {
  const { M, datos } = cargar(process.argv[2] || 'original.html');
  const n = Number(process.argv[3] || 200);
  const t = Date.now();
  const r = duelo(M, datos, () => M.crearRivalReglas(), () => M.crearRivalAzar(), n);
  console.log('Reglas fijas (Normal) vs Azar (Fácil):', r, ((Date.now() - t) / 1000).toFixed(1) + 's');
}

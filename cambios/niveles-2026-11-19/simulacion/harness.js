// Carga el motor y los rivales del index.html sin navegador.
const fs = require('fs');
function cargar(ruta) {
  const lineas = fs.readFileSync(ruta, 'utf8').split('\n');
  const datosLinea = lineas.find((l) => l.includes('__DATOS_JUEGO__') && l.length > 500);
  const m = datosLinea.match(/__DATOS_JUEGO__\s*=\s*/);
  const resto = datosLinea.slice(m.index + m[0].length);
  // el JSON termina en el último "};" o "}"
  let fin = resto.lastIndexOf('}');
  const datos = JSON.parse(resto.slice(0, fin + 1));
  const ini = lineas.findIndex((l) => l.startsWith('// ---- engine/reglas.js ----'));
  const fn = lineas.findIndex((l) => l.startsWith('// ---- ui/datos.js ----'));
  const codigo = lineas.slice(ini, fn).join('\n');
  const nombres = ['crearConfig','nuevaPartida','aplicar','jugadasLegales','crearRivalAzar','crearRivalReglas','crearRivalNivel','NIVELES','nivelPorId','RIVAL','vistaSinMirar','puntuarJugada','PESOS_RIVAL','hayIntervencionLegal','indicesIntervenibles','esPasoAtras','conteoPorCarta','defsDe','danoPendiente','valorSerie'];
  const extra = fs.existsSync(ruta + '.extra') ? '' : '';
  const f = new Function(codigo + '\nreturn {' + nombres.map((n) => `${n}: typeof ${n} !== 'undefined' ? ${n} : undefined`).join(',') + ', __todo: this};');
  return { M: f(), datos };
}
module.exports = { cargar };

const { cargar } = require('./harness.js');
const { duelo } = require('./sim.js');
const ruta = process.argv[2] || 'nuevo.html';
const n = Number(process.argv[3] || 400);
const { M, datos } = cargar(ruta);
const ids = M.NIVELES.map((x) => x.id);
const t = Date.now();
console.log('Victorias (%) de la FILA contra la COLUMNA, ' + n + ' partidas por pareja (colores alternados)\n');
console.log('            ' + ids.map((i) => i.padEnd(10)).join(''));
const mat = {};
for (const a of ids) {
  let fila = a.padEnd(12);
  for (const b of ids) {
    if (a === b) { fila += '   -      '; continue; }
    const r = duelo(M, datos, () => M.crearRivalNivel(a), () => M.crearRivalNivel(b), n, 1000);
    mat[a + '|' + b] = r.pctA;
    fila += (r.pctA * 100).toFixed(0).padStart(3) + '%      ';
  }
  console.log(fila);
}
console.log('\nVecinos (cada nivel vs el anterior):');
for (let i = 1; i < ids.length; i++) console.log(ids[i], 'gana a', ids[i - 1], (mat[ids[i] + '|' + ids[i - 1]] * 100).toFixed(1) + '%');
const r = duelo(M, datos, () => M.crearRivalNivel('maestro'), () => M.crearRivalReglas(), n, 5000);
console.log('Maestro vs Reglas fijas (el Normal de antes):', (r.pctA * 100).toFixed(1) + '%');
console.log(((Date.now() - t) / 1000).toFixed(0) + 's');

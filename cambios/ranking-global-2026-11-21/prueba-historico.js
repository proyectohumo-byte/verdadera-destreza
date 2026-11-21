const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const errores = []; const ll = [];
  const ctx = await b.newContext({ viewport: { width: 420, height: 900 } }); const p = await ctx.newPage();
  p.on('pageerror', (e) => errores.push(e.message));
  await p.route('**/rest/v1/rpc/*', (r) => { const fn = r.request().url().split('/rpc/')[1]; ll.push([fn, r.request().postData()]); r.fulfill({ status: 204, body: '' }); });
  await p.addInitScript(() => { if (!localStorage.getItem('destreza.partidas')) localStorage.setItem('destreza.partidas', JSON.stringify([
    { id: 'a', fecha: '2026-11-20T10:00:00Z', blanco: 'Néstor', negro: 'Ordenador (diestro)', ganador: 'blanco', vida: { blanco: 4, negro: 0 }, vidaInicial: 10, golpes: { blanco: 10, negro: 6 }, dobles: 1, subitas: 0, secuencia: [] },
    { id: 'b', fecha: '2026-11-20T11:00:00Z', blanco: 'Ordenador (maestro)', negro: 'Néstor', ganador: 'blanco', vida: { blanco: 2, negro: 0 }, vidaInicial: 10, golpes: { blanco: 10, negro: 8 }, secuencia: [] },
    { id: 'c', fecha: '2026-11-20T12:00:00Z', blanco: 'Néstor', negro: 'Ordenador (normal)', ganador: 'blanco', vida: { blanco: 4, negro: 0 }, vidaInicial: 10, secuencia: [] },
    { id: 'd', fecha: '2026-11-20T13:00:00Z', blanco: 'Ana', negro: 'Luis', ganador: 'negro', vida: { blanco: 0, negro: 3 }, vidaInicial: 10, secuencia: [] }])); });
  await p.goto('file://' + process.cwd() + '/red-test.html'); await p.waitForTimeout(800);
  await p.fill('#red-apodo', 'Néstor'); await p.click('[data-accion=red-si]');
  await p.waitForTimeout(13000);
  console.log(ll.map(([f, b]) => f + ' ' + (b ?? '').replace(/"p_cliente":"[^"]+",/, '')).join('\n'));
  console.log('cola:', await p.evaluate(() => localStorage.getItem('destreza.redCola')));
  await p.reload(); await p.waitForTimeout(1500);
  console.log('tras recargar, llamadas totales:', ll.length, '(no debe repetir el histórico)');
  console.log('ERRORES:', errores.length ? errores : 'ninguno');
  await b.close();
})();

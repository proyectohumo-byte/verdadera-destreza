const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const errores = [];
  const llamadas = [];
  let modo = 'ok';
  const nuevaPag = async () => {
    const ctx = await b.newContext({ viewport: { width: 420, height: 900 } });
    const p = await ctx.newPage();
    p.on('pageerror', (e) => errores.push('pageerror: ' + e.message));
    await p.route('**/rest/v1/rpc/*', async (r) => {
      const fn = r.request().url().split('/rpc/')[1];
      const body = r.request().postData();
      const key = r.request().headers()['apikey'];
      if (modo === 'caido') return r.abort();
      llamadas.push({ fn, body: body && JSON.parse(body), key });
      if (fn === 'ranking_global') return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([{ apodo: 'Tester <b>', partidas: 3, ganadas: 2, puntos: 5, tocados: 20, ultima: 'x' }]) });
      return r.fulfill({ status: 204, body: '' });
    });
    return { ctx, p };
  };
  const url = 'file://' + process.cwd() + '/red-test.html';
  // 1. Primera vez: aviso y participar
  let { ctx, p } = await nuevaPag();
  await p.goto(url); await p.waitForTimeout(800);
  console.log('aviso visible:', await p.isVisible('#dlg-red'), '| llamadas antes de aceptar:', llamadas.length);
  await p.fill('#red-apodo', 'Tester');
  await p.click('[data-accion=red-si]'); await p.waitForTimeout(400);
  console.log('visita:', JSON.stringify(llamadas.map((l) => [l.fn, l.body])), 'clave enviada:', llamadas[0]?.key?.slice(0, 15));
  // 2. Partida contra Diestro y fin
  await p.click('button[value=empezar]'); await p.waitForTimeout(1500);
  await p.evaluate(() => { window.__t.ui.inicioPartida = Date.now() - 95000; window.__t.registrarResultado({ ganador: window.__t.ui.abajo, vida: { blanco: 3, negro: 0 } }); });
  await p.waitForTimeout(600);
  console.log('partida enviada:', JSON.stringify(llamadas.filter((l) => l.fn === 'registrar_partida').map((l) => l.body)));
  // 3. Ranking global
  await p.evaluate(() => document.querySelector('[data-accion=ranking]').click()); await p.waitForTimeout(300);
  await p.click('[data-accion=red-ranking]'); await p.waitForTimeout(500);
  console.log('ranking:', (await p.$eval('#red-contenido', (e) => e.innerText)).replace(/\s+/g, ' ').slice(0, 220));
  console.log('XSS escapado:', (await p.$eval('#red-contenido', (e) => e.innerHTML)).includes('Tester &lt;b&gt;'));
  await p.screenshot({ path: 'red-ranking.png' });
  // 4. Sin conexión: cola y reintento
  await p.click('[data-accion=red-cerrar]');
  modo = 'caido'; llamadas.length = 0;
  await p.evaluate(() => { window.__t.ui.nombres[window.__t.ui.ladoOrdenador] = 'Ordenador (maestro)'; window.__t.registrarResultado({ ganador: window.__t.ui.ladoOrdenador, vida: { blanco: 0, negro: 5 } }); });
  await p.waitForTimeout(500);
  console.log('cola sin conexión:', await p.evaluate(() => JSON.parse(localStorage.getItem('destreza.redCola')).map((x) => x.p_nivel + ':' + x.p_gano)));
  modo = 'ok'; await p.reload(); await p.waitForTimeout(1500);
  console.log('tras reconectar:', llamadas.map((l) => l.fn).join(','), '| cola:', await p.evaluate(() => localStorage.getItem('destreza.redCola')));
  await ctx.close();
  // 5. "No, gracias"
  llamadas.length = 0;
  ({ ctx, p } = await nuevaPag());
  await p.goto(url); await p.waitForTimeout(800);
  await p.click('[data-accion=red-no]'); await p.click('button[value=empezar]'); await p.waitForTimeout(1200);
  await p.evaluate(() => window.__t.registrarResultado({ ganador: window.__t.ui.abajo, vida: { blanco: 3, negro: 0 } }));
  await p.waitForTimeout(500);
  console.log('no participa -> llamadas:', llamadas.length);
  await p.reload(); await p.waitForTimeout(800);
  console.log('no vuelve a preguntar:', !(await p.isVisible('#dlg-red')));
  console.log('ERRORES:', errores.length ? errores : 'ninguno');
  await b.close();
})();

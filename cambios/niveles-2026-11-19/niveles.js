// ---- rival/niveles.js ---- (NUEVO: cinco niveles de dificultad)
// Ningún nivel ve la mano del rival. Cada nivel limita tres cosas de lo que hoy hace "Reglas fijas":
//   - atención: solo evalúa K jugadas elegidas al azar (K = 0: todas);
//   - memoria: solo recuerda las cartas jugadas por el rival en las últimas `memoria` series del ciclo,
//     y cada una con probabilidad `fidelidad` (si no, la da por no jugada: cree que aún puede tenerla);
//   - sutilezas de reglas que anticipa del rival (candado, límite del Reparo, corte del paso atrás).
// Además, `ruido` es el azar añadido a cada puntuación (en "Reglas fijas" es 0,4) y `despiste` es la
// probabilidad de que en una decisión juegue una jugada legal al azar, como un despiste.
// Los parámetros están todos aquí, en NIVELES, para ajustarlos sin tocar nada más.

const NIVELES = [
  { id: 'bisono', nombre: 'Bisoño', frase: 'Mozo recién llegado a la sala de armas: empuña la espada con respeto, pero poco sabe de ella.',
    K: 2, ruido: 3, despiste: 0.7, memoria: 0, fidelidad: 1, sutilezas: { candado: false, reparo: false, pasoAtras: false } },
  { id: 'discipulo', nombre: 'Discípulo', frase: 'Aprende el compás bajo la vista del maestro: atiende a la estocada que tiene delante, no a la que vendrá.',
    K: 3, ruido: 2, despiste: 0.5, memoria: 0, fidelidad: 1, sutilezas: { candado: false, reparo: false, pasoAtras: false } },
  { id: 'diestro', nombre: 'Diestro', frase: 'Hombre ya ducho en la ciencia de las armas: guarda memoria de tus últimas jugadas, aunque la memoria a veces le falla.',
    K: 6, ruido: 1, despiste: 0.25, memoria: 2, fidelidad: 0.75, sutilezas: { candado: true, reparo: false, pasoAtras: false } },
  { id: 'preboste', nombre: 'Preboste', frase: 'Ayudante del maestro, con licencia para enseñar en su ausencia: lleva buena cuenta de las cartas, sin llegar a la certeza.',
    K: 12, ruido: 0.7, despiste: 0.1, memoria: 4, fidelidad: 0.85, sutilezas: { candado: true, reparo: true, pasoAtras: false } },
  { id: 'maestro', nombre: 'Maestro', frase: 'Examinado en el arte y respetado en la plaza: casi nada se le escapa, pero ni ve tu mano ni es infalible.',
    K: 0, ruido: 0.4, despiste: 0.03, memoria: 99, fidelidad: 0.95, sutilezas: { candado: true, reparo: true, pasoAtras: true } },
];
const NIVEL_POR_DEFECTO = 'diestro';

function nivelPorId(id) {
  if (id === 'azar') id = 'bisono'; // compatibilidad con partidas guardadas: Fácil
  if (id === 'reglas') id = 'maestro'; // compatibilidad: Normal
  return NIVELES.find((n) => n.id === id) ?? NIVELES.find((n) => n.id === NIVEL_POR_DEFECTO);
}

function crearRivalNivel(id) {
  const niv = nivelPorId(id);
  if (niv.azar) {
    const r = crearRivalAzar();
    return { ...r, nombre: niv.nombre, nivel: niv.id };
  }
  const P = { ...PESOS_RIVAL, azar: 0 };
  return {
    nombre: niv.nombre,
    nivel: niv.id,
    elegir(estado, rng = Math.random) {
      const js = jugadasLegales(estado);
      if (js.length === 1) return js[0];
      if (niv.despiste && rng() < niv.despiste) return js[Math.floor(rng() * js.length)];
      const cand = niv.K && js.length > niv.K ? muestraAleatoria(js, niv.K, rng) : js;
      let mejor = cand[0];
      let mejorP = -Infinity;
      for (const j of cand) {
        const p = puntuarJugadaNivel(estado, j, P, niv, rng) + rng() * niv.ruido;
        if (p > mejorP) {
          mejorP = p;
          mejor = j;
        }
      }
      return mejor;
    },
  };
}

function muestraAleatoria(lista, k, rng) {
  const a = [...lista];
  for (let i = 0; i < k; i++) {
    const s = i + Math.floor(rng() * (a.length - i));
    [a[i], a[s]] = [a[s], a[i]];
  }
  return a.slice(0, k);
}

/**
 * Lo que el bot cree del rival: todas las cartas que no ve en la mesa (mano + pila, sin distinguirlas),
 * más las que ha olvidado que ya se jugaron. Con poca fidelidad también "pierde" alguna carta posible.
 */
function vistaImperfecta(estado, otro, niv, rng) {
  const sinVer = [...estado.mano[otro], ...(estado.pila?.[otro] ?? [])];
  const olvidadas = [];
  for (const g of estado.mesa[otro]) {
    const edad = estado.contadores.series - g.orden;
    for (const c of g.cartas) {
      if (edad > niv.memoria || rng() >= niv.fidelidad) olvidadas.push(c);
    }
  }
  const mano = [...sinVer, ...olvidadas];
  if (niv.fidelidad < 1 && mano.length > 1 && rng() < (1 - niv.fidelidad) / 2) {
    mano.splice(Math.floor(rng() * mano.length), 1); // da por jugada una carta que quizá aún tiene
  }
  return { ...estado, mano: { ...estado.mano, [otro]: mano } };
}

function primeraValidaNivel(def, serie, indice, suma, pasoAtrasDisponible, sut) {
  if (!puedeEmpezarContra(def, serie, indice)) return false;
  if (!estrellaQueInterviene(def, serie, indice)) return false;
  if (sut.candado && aEspadaSujeta(def, serie, indice)) return false;
  if (sut.reparo && !cumpleSumaRival(def, def.limiteEnCartas ? medidaRival(def, serie) : suma)) return false;
  if (def.pasoAtras && !pasoAtrasDisponible) return false;
  return true;
}

/** Como indicesIntervenibles y hayIntervencionLegal, pero anticipando solo las sutilezas del nivel. */
function indicesIntervenibles_nivel(estado, sut) {
  if (estado.fase !== 'responder') return [];
  const cfg = estado.config;
  const j = estado.turno;
  const serie = defsDe(cfg, estado.serieDeclarada.cartas);
  const suma = valorSerie(serie);
  const conteo = conteoPorCarta(cfg, estado.mano[j]);
  const res = [];
  for (let indice = 0; indice < serie.length; indice++) {
    for (const id of Object.keys(conteo)) {
      if (primeraValidaNivel(cfg.cartas[id], serie, indice, suma, estado.pasoAtrasDisponible[j], sut) && tieneSerieCompleta(cfg, conteo, id)) {
        res.push(indice);
        break;
      }
    }
  }
  return res;
}

function puntuarJugadaNivel(estado, jugada, P, niv, rng) {
  const cfg = estado.config;
  const yo = estado.turno;
  const otro = RIVAL[yo];
  const sut = niv.sutilezas;
  if (jugada.tipo === 'noIntervenir') {
    const sd = estado.serieDeclarada;
    if (esPasoAtras(cfg, sd.cartas)) return 0;
    if (esParadaSinHerida(cfg, sd.cartas)) return cfg.ajustes.reparoSinRespuesta === 'C' ? -P.puntoMuertoGanado : P.puntoMuertoGanado;
    const dano = danoPendiente(estado).dano;
    if (dano >= estado.vida[yo]) return -1000;
    return -dano * P.recibir;
  }
  const real = aplicar(estado, jugada);
  if (real.fase === 'fin') return real.empate ? -100 : real.ganador === yo ? 1000 : -1000;
  if (real.eventos.some((ev) => ev.tipo === 'golpeDoble')) return P.golpeDoble;
  if (esParadaSinHerida(cfg, jugada.cartas)) return P.paradaSinHerida;
  const sig = vistaImperfecta(real, otro, niv, rng);
  if (esPasoAtras(cfg, jugada.cartas)) {
    const cortable = sut.pasoAtras && indicesIntervenibles_nivel(sig, sut).length > 0;
    return cortable ? P.pasoAtrasCortable : P.pasoAtrasSeguro;
  }
  const ac = cfg.ajustes.aperturaCercana;
  const abreCerca = jugada.tipo === 'declarar' && ac.cartas.includes(cfg.cartaDe[jugada.cartas[0]]);
  const coste = (estado.vida[yo] - real.vida[yo]) * P.recibir + (abreCerca ? ac.heridaExtraRecibida * P.recibir * 0.5 : 0);
  const dano = danoDeSerie(estado, yo, jugada.cartas, jugada.tipo === 'declarar').dano;
  const expuestas = indicesIntervenibles_nivel(sig, sut).length;
  if (expuestas === 0) {
    if (dano >= estado.vida[otro]) return 1000;
    return dano * P.heridaSegura + 2 - coste;
  }
  const extra = cfg.ajustes.roboExtraSerieLarga;
  const netas = jugada.cartas.length - (extra.cartas && jugada.cartas.length >= extra.desde ? extra.cartas : 0);
  return dano * P.dano - expuestas * P.exposicion - netas * P.cartas - coste;
}


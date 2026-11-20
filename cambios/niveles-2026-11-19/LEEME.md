# Cambios: cinco niveles de dificultad (19/11/2026)

Este archivo describe los cambios probados en una copia del juego para que se puedan reproducir en el proyecto real. Nada de esta carpeta modifica el `index.html` publicado.

## Para quien vaya a aplicarlos (Claude Code)

El `index.html` de este repositorio es el juego compilado en un solo archivo. El proyecto fuente (con los módulos `engine/`, `rival/`, `ui/`, y la carpeta `sim/` con `npm run simular`) no está aquí. Aplica los cambios en el proyecto fuente, no en este archivo, o la próxima publicación los borrará.

Antes de tocar nada, confirma que lo descrito aquí coincide con tu código (nombres de funciones, línea del selector de nivel). Si algo no coincide, dímelo y no lo fuerces.

## Qué problema resuelve

El ordenador "Normal" jugaba demasiado bien. Lo que lo hacía fuerte, según el código:

1. Evalúa **todas** las jugadas legales y puntúa cada una (`jugadasLegales` y `puntuarJugada`).
2. Deduce la mano del rival por descarte con **memoria perfecta** (`vistaSinMirar`): supone que tiene todas las cartas que no ve en la mesa.
3. Conoce todas las reglas sutiles (candado, límite del Reparo, corte del paso atrás con Estocada).
4. Apenas tiene azar (0,4 sobre la puntuación).

No ve la mano del rival: se comprobó que `vistaSinMirar` mezcla mano y pila del rival y solo equivale a "mazo menos mesa". Por eso la solución no es ocultarle la mano, sino limitar su atención, su memoria y su conocimiento de las reglas.

## Qué se ha cambiado

Todo es aditivo, salvo las líneas del punto 2. No se toca el motor (`engine/`) ni `puntuarJugada`, `crearRivalReglas` o `crearRivalAzar`.

1. **Módulo nuevo `rival/niveles.js`**, copia exacta en `niveles.js` de esta carpeta. Va en el proyecto fuente como un módulo más, después de `rival/reglas-fijas.js`. Define `NIVELES`, `nivelPorId`, `crearRivalNivel` y las funciones auxiliares. Usa `PESOS_RIVAL`, `crearRivalAzar`, `jugadasLegales`, `aplicar`, `danoDeSerie`, `danoPendiente` y las funciones del motor que ya existen.
2. **Selector y creación del rival** (en `ui/app.js` y en la plantilla HTML de "Nueva partida"):
   - Sustituir los dos radios Normal/Fácil por cinco radios con `name="nivel"` y valores `bisono`, `discipulo`, `diestro` (marcado por defecto), `preboste` y `maestro`.
   - En `empezarPartida`: `ui.rival = crearRivalNivel(f.get('nivel'));`
   - El nombre del rival en el historial: `` `Ordenador (${nivelPorId(f.get('nivel')).nombre.toLowerCase()})` ``
   - En `iniciar`: `ui.rival = crearRivalNivel(NIVEL_POR_DEFECTO);`
   - `nivelPorId` traduce los valores antiguos (`azar` pasa a Bisoño y `reglas` a Maestro) para no romper nada guardado.
4. **Suma sobre la serie declarada** (en el renderizado de la pista, `ui/vista.js`): la etiqueta "suma N" de la primera carta de la serie declarada muestra ahora el daño pendiente completo (`danoPendiente(e).dano`: suma de la serie, +1 si contesta una carta del rival, y la herida extra por apertura cercana), no solo `.suma`. El detalle sale en el `title`. Pedido por el autor el 20/11/2026.

5. **Partida en curso guardada** (`ui/app.js`): `guardarEnCurso()` se llama al principio de `render()` y guarda en `localStorage` (clave `destreza.enCurso`) el estado de la partida (sin `config`, que se reconstruye con `crearConfig(cartas, ajustes)`), los ajustes de la partida (`ui.ajustesPartida`, nuevo, se asigna en `empezarPartida`), el nivel del rival, los nombres, la pausa y el registro. `retomarEnCurso()` se llama en `iniciar()` justo antes del primer `render()`: si hay partida guardada, la restaura y no abre el diálogo de "Nueva partida"; si el guardado está corrupto, lo borra y arranca como siempre. Al terminar la partida (`fase === 'fin'`) se borra el guardado, porque ya queda en el Historial. Probado en navegador: recargar a mitad de partida conserva vida, mano, pista y registro. Pedido por el autor el 20/11/2026 para no perder la partida al recargar entre versiones.

6. **Ayuda en las cabeceras del ranking** (`abrirRanking` en `ui/app.js` y el CSS de `.tabla-ranking`): las columnas P, G, E, Pe, %, Tocados y # llevan `data-ayuda` y `tabindex="0"`, y al pasar el ratón o pulsar se muestra un globo con la explicación (por ejemplo "Partidas ganadas"). Sustituye a los `title`, que no se ven en móvil. Pedido por el autor el 20/11/2026.

7. **Resultados contra cada rival** (`htmlEnfrentamientos`, nueva, llamada desde `abrirRanking` en `ui/app.js`): bloque desplegado por defecto, encima del ranking por esgrimista, con una fila por pareja "esgrimista contra rival" (por ejemplo "Néstor contra Ordenador (diestro)") y las columnas P, G, E, Pe, %, Tocados. Las filas del ordenador se omiten. Los rivales del ordenador salen ordenados por nivel (bisoño a maestro). Se apoya en que el nombre del rival en el Historial es `Ordenador (nivel)`. Ambos bloques de ranking van **encima** de la lista de partidas (orden en `abrirRanking`: `htmlEnfrentamientos(todas) + ranking + filtros + partidas`), para no tener que bajar por un historial largo. Pedido por el autor el 20/11/2026.

8. **Cruz de cierre en las ventanas** (`iniciar` en `ui/app.js` y CSS `.cerrar-x`): al arrancar se añade un botón "×" arriba a la derecha de cada `<dialog>` (Nueva partida, Historial, Cómo jugar), que llama a `d.close()`. Queda fija arriba al desplazar el contenido. Pedido por el autor el 20/11/2026.

9. **Tocados contados desde la crónica, incluida la muerte súbita** (`ui/app.js`). Antes los tocados eran "vida inicial - vida final", que no ve los puntos perdidos antes de una muerte súbita (los dos vuelven a 1). Ahora:
   - `golpesDeCronica(p)` (nueva) recorre la crónica de la partida (`p.secuencia`: pasos `herida` y `doble`) y suma los puntos realmente perdidos, contando la vida previa a cada reinicio. No tiene que ser exacto al milímetro: refleja lo que cuenta la crónica.
   - **Se calcula una sola vez, al terminar la partida**: `registrarResultado` guarda el resultado en la propia partida (`golpes: { blanco, negro }`). `calcularRanking` y `htmlEnfrentamientos` solo suman `p.golpes`; no recalculan nada al abrir el Historial. Si una partida no tiene `golpes`, usan el cálculo antiguo.
   - **PARCHE TEMPORAL, solo para la versión de prueba: `migrarGolpesPartidasAntiguas()`**, llamada al principio de `iniciar`. Rellena una sola vez el `golpes` de las partidas ya guardadas que no lo tienen (las de antes de este cambio), a partir de su crónica, y las guarda. **No llevar a la versión final**: allí todas las partidas se registrarán ya con `golpes`, así que esta función y su llamada deben borrarse.
   - La partida en curso guarda y restaura también su crónica (`secuencia`), para que los tocados de una partida retomada tras recargar no se pierdan.
   Pedido por el autor el 20/11/2026.

10. **Columnas DT y MS en lugar de E** (`calcularRanking`, `htmlEnfrentamientos`, cabeceras de ambas tablas, `ui/app.js`): como no se puede empatar (muerte súbita), la columna "E" (empates) se quita de las dos tablas y se sustituye por **DT** (dobles tocados, Estocada contra Estocada, incluidas las muertes súbitas) y **MS** (muertes súbitas). Orden de columnas: P, G, Pe, DT, MS, %, Tocados. Igual que los tocados, se cuentan **una sola vez al terminar la partida** con `contarDobles(p)` (nueva, desde la crónica) y se guardan en la partida (`dobles`, `subitas`); las tablas solo suman lo guardado. El parche temporal `migrarGolpesPartidasAntiguas()` rellena también estos dos datos en las partidas antiguas (borrar en la versión final, ver cambio 9). El código sigue admitiendo `ganador === null` por seguridad, pero ya no se muestra. Pedido por el autor el 20/11/2026.

El script `aplicar-parches.py` aplica exactamente esos cambios al `index.html` compilado, y se ha comprobado que reproduce el archivo de prueba byte a byte. Sirve como referencia de los textos exactos.

## Cómo funciona cada nivel

Ningún nivel ve la mano del rival. Cada nivel limita cinco parámetros, todos en `NIVELES` (para ajustarlos sin tocar código):

| Parámetro | Qué hace |
|---|---|
| `K` | Número de jugadas legales que evalúa, elegidas al azar (0 = todas). |
| `ruido` | Azar añadido a cada puntuación (en "Reglas fijas" era 0,4). |
| `despiste` | Probabilidad de que en una decisión juegue una jugada legal al azar. |
| `memoria` y `fidelidad` | Solo recuerda las cartas que el rival jugó en las últimas `memoria` series, y cada una con probabilidad `fidelidad`. Las olvidadas cuentan como cartas que el rival aún puede tener, y con fidelidad baja a veces "pierde" una carta posible. |
| `sutilezas` | Qué reglas anticipa del rival: `candado`, `reparo` (límite del Reparo menor que 4) y `pasoAtras` (corte del Compás con Estocada). Nunca juega ilegalmente. |

Parámetros añadidos en la segunda ronda (todos opcionales, por nivel):

| Parámetro | Qué hace |
|---|---|
| `miedo` | Bonus al Reparo, al Compás y a las series cortas. Solo Bisoño (3). |
| `largo` | Bonus por cada carta de la serie: saber enlazar cadenas. Discípulo 0,3; Diestro 1,2; Preboste 0,5. |
| `prevision` | Resta una fracción de la mejor respuesta que cree que tendría el rival. Solo Maestro (0,2). |
| `cargar` / `cargarPen` | Probado y descartado (ver abajo). Valen 0 en todos los niveles. |

Valores finales:

| Nivel | K | ruido | despiste | memoria | fidelidad | candado | reparo | paso atrás | extra |
|---|---|---|---|---|---|---|---|---|---|
| Bisoño | 2 | 3 | 0,7 | 0 | 1 | no | no | no | miedo 3 |
| Discípulo | 3 | 2 | 0,5 | 0 | 1 | no | no | no | largo 0,3 |
| Diestro | 6 | 1 | 0,25 | 2 | 0,75 | sí | no | no | largo 1,2 |
| Preboste | 12 | 0,7 | 0,1 | 4 | 0,85 | sí | sí | no | largo 0,5 |
| Maestro | todas | 0,4 | 0,03 | todo el ciclo | 0,95 | sí | sí | sí | previsión 0,2 |

## Cómo se comprobó

Se cargó el motor sin navegador (`simulacion/harness.js`) y se enfrentaron los niveles entre sí con colores y primer turno alternados (`simulacion/torneo.js`, resultados completos en `simulacion/resultados.txt`).

Mano de 5 cartas, 1500 partidas por pareja (`simulacion/resultados-v2.txt`, script `simulacion/torneo-escalera-y-vieja.js`). Victorias del nivel superior sobre el inferior:

| Pareja | Victorias |
|---|---|
| Discípulo contra Bisoño | 63,8 % |
| Diestro contra Discípulo | 66,7 % |
| Preboste contra Diestro | 60,1 % |
| Maestro contra Preboste | 60,9 % |

Contra la IA antigua (reglas fijas, el "Normal" de antes) y contra el azar puro:

| Nivel | Gana a la antigua | 
|---|---|
| Bisoño | 9 % (gana al azar puro un 62 %) |
| Discípulo | 17 % |
| Diestro | 27 % |
| Preboste | 36 % |
| Maestro | 48 % |

**Resultado honesto sobre "que el Maestro le dé una paliza a la antigua": no se ha conseguido.** El Maestro queda en paridad (48 %, hasta 51 % en pruebas con memoria perfecta). Se probó: (1) cargar la serie solo si el rival no puede contestar (`cargar`): sin efecto, porque la evaluación ya multiplica el daño en ese caso, y penalizar las series largas cuando sí puede contestar hunde al Maestro (hasta 34 %); (2) reajustar los pesos uno a uno: la antigua ya está en un óptimo local; (3) mirar la respuesta del rival (`prevision`): da 1-3 puntos. La antigua usa la misma información y el mismo evaluador, y con manos de 5 cartas hay mucha suerte. Para ganarle con claridad hace falta búsqueda real (simular varias manos posibles y jugar partidas hasta el final), que es otro nivel de complejidad y acerca el Maestro a "saberlo todo", cosa que el autor no quería.

Con "todas las cartas en la mano" las diferencias son mayores, entre 70 % y 76 %, porque las partidas son mucho más largas.

Prueba de humo en un navegador sin cabeza: se muestran los cinco niveles, el ordenador mueve, sin errores en consola.

## Pendiente y decisiones abiertas

- El primer escalón (Discípulo contra Bisoño) queda en 64 %, bajo el 70 % buscado; es el precio de que Bisoño ya no sea azar puro.
- No se ha implementado "mira una jugada por delante" ni "gestiona reservas" para Preboste y Maestro. La evaluación existente ya penaliza las cartas que deja expuestas y las que gasta, que es lo que produce ese estilo prudente. Si se quiere un Maestro más fuerte, es el sitio para añadirlo.
- Falta el registro de victorias del jugador por nivel en el Historial. Es una mejora independiente y sirve para ajustar los parámetros con partidas reales.
- Los nombres de nivel (Bisoño, Discípulo, Diestro, Preboste, Maestro) son los elegidos por el autor. Los textos explicativos de cada uno están en `NIVELES[].frase` y en el selector.
- La regla del candado, las 13 cartas y el resto de diferencias con el documento de reglas original (`instrucciones-claude-code.md`) están pendientes de confirmar por el autor.

## Para una segunda versión (decidido por el autor el 19/11/2026)

Para la primera versión se deja el Maestro como está: igual de fuerte que la IA antigua (48 %), sin la búsqueda pesada.

Si más adelante hace falta un Maestro claramente superior (por ejemplo, ya con el juego muy avanzado y pensando en publicar una app), la idea es que **el Maestro juegue partidas enteras por su lado**: en cada decisión, sortear varias manos posibles del rival coherentes con lo que ha visto, jugar cada candidata hasta el final contra un rival sencillo y elegir la jugada con más victorias. Advertencias:
- Es mucho más lento; habría que limitar el número de manos y partidas por decisión, sobre todo en móvil.
- Se acerca a "saberlo todo", que el autor no quería para el Maestro; conviene mantener memoria imperfecta al sortear las manos.
- Se medirá con `simulacion/torneo-escalera-y-vieja.js` y debería superar el 60 % contra la IA antigua sin romper la escalera.
- Los parámetros `cargar` y `cargarPen` quedan en 0; se probaron y no sirven (ver arriba).


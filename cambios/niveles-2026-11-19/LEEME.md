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
3. **Aviso del Compás** (en `htmlMarcador`): si el jugador humano tiene el paso atrás sin gastar pero la carta Compás no está en su mano, el marcador añade "(el Compás no está en tu mano)". No se muestra para el ordenador, para no revelar su mano.

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

Valores finales:

| Nivel | K | ruido | despiste | memoria | fidelidad | candado | reparo | paso atrás |
|---|---|---|---|---|---|---|---|---|
| Bisoño | jugada legal al azar | | | | | | | |
| Discípulo | 3 | 2 | 0,5 | 0 | 1 | no | no | no |
| Diestro | 6 | 1 | 0,25 | 2 | 0,75 | sí | no | no |
| Preboste | 12 | 0,7 | 0,1 | 4 | 0,85 | sí | sí | no |
| Maestro | todas | 0,4 | 0,03 | todo el ciclo | 0,95 | sí | sí | sí |

## Cómo se comprobó

Se cargó el motor sin navegador (`simulacion/harness.js`) y se enfrentaron los niveles entre sí con colores y primer turno alternados (`simulacion/torneo.js`, resultados completos en `simulacion/resultados.txt`).

Mano de 5 cartas, 1000 partidas por pareja, victorias del nivel superior sobre el inmediatamente inferior:

| Pareja | Victorias |
|---|---|
| Discípulo contra Bisoño | 72,8 % |
| Diestro contra Discípulo | 67,9 % |
| Preboste contra Diestro | 58,8 % |
| Maestro contra Preboste | 58,2 % |

El Maestro empata con el antiguo "Normal" (48 %), por lo que sigue siendo el nivel más difícil. Ningún nivel gana al anterior por menos de 55 %.

Con "todas las cartas en la mano" las diferencias son mayores, entre 70 % y 76 %, porque las partidas son mucho más largas.

Prueba de humo en un navegador sin cabeza: se muestran los cinco niveles, el ordenador mueve, sin errores en consola, y el aviso del Compás aparece solo para el jugador humano.

## Pendiente y decisiones abiertas

- El primer escalón (Discípulo contra Bisoño) queda en 73 %, algo por encima del 70 % buscado. Bisoño es aleatorio puro y cualquier evaluación le gana con facilidad.
- No se ha implementado "mira una jugada por delante" ni "gestiona reservas" para Preboste y Maestro. La evaluación existente ya penaliza las cartas que deja expuestas y las que gasta, que es lo que produce ese estilo prudente. Si se quiere un Maestro más fuerte, es el sitio para añadirlo.
- Falta el registro de victorias del jugador por nivel en el Historial. Es una mejora independiente y sirve para ajustar los parámetros con partidas reales.
- Los nombres de nivel (Bisoño, Discípulo, Diestro, Preboste, Maestro) son los elegidos por el autor. Los textos explicativos de cada uno están en `NIVELES[].frase` y en el selector.
- La regla del candado, las 13 cartas y el resto de diferencias con el documento de reglas original (`instrucciones-claude-code.md`) están pendientes de confirmar por el autor.

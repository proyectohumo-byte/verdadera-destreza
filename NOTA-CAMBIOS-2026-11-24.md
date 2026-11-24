# Cambios del 24/11/2026 (hechos directamente en index.html)

Están ya publicados en `index.html`, pero **no en el código fuente** (`ui/*.js`, hoja de estilos).
Si se vuelve a generar `index.html` con `scripts/construir.js` sin pasarlos antes al código fuente, se pierden.

## 1. Mesa: quién contesta a quién (ui/app.js, función `htmlPista` y `render`)
- Cada serie de la mesa lleva un número (1, 2, 3… por combate), el mismo que en la crónica (`registrar` guarda `n` y `serie`).
- Una línea con flechas une cada respuesta con la carta que interviene: función nueva `dibujarEnlaces()`, que se llama en `render()` después de pintar la pista y al cambiar el tamaño de la ventana.
- Al pasar el ratón por una entrada de la crónica se resaltan sus cartas y su línea (`resaltarSerie`).
- CSS nuevo: `.num-serie`, `.enlaces`, `.celda.resaltada`. Las filas de la pista tienen más hueco lateral (`.pista .fila`).

## 2. Bienvenida y arranque (ui/app.js `iniciar`, HTML `#dlg-bienvenida`)
- La primera vez sale una ventana con tres ideas y los botones «Partida de aprendizaje», «Jugar ya» y «Leer Cómo jugar». Se recuerda en `localStorage` (`destreza.bienvenida`).
- Con `?bienvenida` en la dirección sale siempre.
- Arreglo: el ordenador ya no juega por detrás del menú inicial. Hasta pulsar «Empezar» la mesa está en espera (`ui.enEspera`), y «Cancelar» la deja así.

## 3. Partida de aprendizaje (ui/app.js, bloque `TUTORIAL`)
- Siempre la misma: semilla 12679, 5 de vida, empieza Blanco. El rival sigue un guion (`crearRivalTutorial`) y a la persona solo se le deja hacer la jugada del guion (`permiteTutorial`, comprobado en `comprobarSeleccion`, `respuestaSobreRival`, `alPulsarRival` y `jugar`).
- Panel con las instrucciones entre la pista y la mano (`htmlTutor`). En el móvil solo se ve la orden corta, y la explicación se abre con un botón.
- No se guarda en el Historial ni como partida en curso.
- Botón «Partida de aprendizaje» también en la ventana de Nueva partida.
- Textos en español y portugués (los del panel están en `TUTORIAL.es` / `TUTORIAL.pt`; el resto, en `FRASES_PT` de ui/pt.js).
- **Ojo:** si cambian las reglas, las cartas o el barajado, el guion puede dejar de cuadrar. Hay que volver a comprobarlo.

## 4. Versión
- `__VERSION_JUEGO__` y `sw.js` pasan a 20261124120000.

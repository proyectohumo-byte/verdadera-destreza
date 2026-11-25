# Historial de cambios del juego

Un solo archivo para todas las versiones: la más reciente arriba.
Cada vez que se cambie algo, se añade aquí una entrada nueva y no se borra ninguna de las anteriores.
El juego entero está en `index.html`: ese es el archivo que se cambia.

---

## 25/11/2026 · Partidas con todas las cartas: cuentan media

- **Por qué:** con todas las cartas en la mano no hay suerte en el robo y se sabe qué tiene el rival; gana mucho más quien lee mejor el lance (simulación: Maestro contra Bisoño, 89 % con mano de 5 y 98,5 % con todas).
- **Qué cambia:** cada partida con todas las cartas cuenta como media partida en todo: título (fuerza y categorías), Historial (P, G, Pe y %) y ranking global. Ganar con todas sigue subiendo, pero menos. Las cifras con media salen con coma (8,5).
- Cada partida guarda ahora `mano` (5 o 'todas') en `registrarResultado`; las antiguas, sin ese dato, cuentan como de 5. `pesoPartida` y `cifraPartidas` en el bloque de ranking; `tituloEsgrimista` pondera con `w`.
- **Panel del autor (autor.html):** cada jugador muestra sus partidas y su % con 5 cartas y con todas (en naranja si juega sobre todo con todas, desde 5 partidas); cada nivel, una línea más para las de todas; la columna «Mano» en las últimas partidas; y el % de partidas con todas en el resumen. `panel_autor` en Supabase actualizado.
- Ranking global: se manda `p_todas` y `todas` en el histórico. En Supabase se ejecutó `servidor/mano-todas.sql` del código fuente (columna `todas`, `ranking_global` con medias).

## Versión 20261125120000 · 25/11/2026 · Paso atrás a la vista y mano entera en apaisado

- **Paso atrás:** vuelve a verse «Paso atrás: disponible / usado» en el móvil (el rediseño lo había ocultado). Va debajo de la marca de turno, fuera de ella y en gris. `htmlMarcador` envuelve cada lado en `.lado` con la `.vida` y, debajo, el `.paso`.
- **Móvil en apaisado:** la mano se ve entera; antes asomaba solo la parte de arriba de las cartas (`.zona-abajo` sin margen negativo y `--w` algo menor en `@media (max-height: 520px)`).

## Versión 20261125100000 · 25/11/2026 · Cabecera y × de quitar

- **Rival con su nivel:** en la cabecera pone «Negro (Preboste)», «Negro (Bisoño)», etc., en lugar de «(ordenador)» (`htmlMarcador`).
- **Marca de turno en el móvil:** cuando el nombre ocupa dos líneas, el recuadro ya no es una pastilla redonda que corta las letras: esquinas de 14 px y algo más de margen (`.vida` y `.vida-nombre` en `@media (max-width: 700px)`).
- **× de quitar:** las cartas de tu mano que ya están en la serie llevan una × encima, para que se vea que al tocarlas se quitan (con las que van detrás). `htmlZona` añade `<span class="quitar-x">` y CSS `.quitar-x`.

## Versión 20261124150000 · 24/11/2026 · Rediseño

- **Pantalla de app:** la página ya no se desplaza. Arriba, las dos vidas y dos botones (📄 crónica y ☰ menú); en medio, la mesa; abajo, tu mano, siempre en su sitio y más grande.
- **Menú ☰:** Nueva partida, Partida de aprendizaje, Cómo jugar, Historial e idioma.
- **La mesa se mueve por dentro:** sigue sola la jugada (la línea de combate y las filas en juego siempre a la vista). Lo viejo se aparta hacia los bordes; se puede mirar arrastrando la mesa con el dedo o el ratón, y al soltarla vuelve sola a la jugada.
- **Crónica:** pasa a un cajón lateral que se abre con su botón. El último movimiento sale un momento en un aviso sobre la mesa.
- **Móvil en horizontal:** ahora se puede (antes estaba bloqueado en vertical). La mano asoma por abajo y el panel del aprendizaje va en una esquina.
- **Estilo:** títulos en letra de tratado (Cormorant Garamond) y el resto en letra limpia (Inter), sin marcos dobles ni versalitas, botones redondeados.
- Las cartas del rival siguen giradas, como en la mesa real, para que encajen círculos, flechas y estrellas.

## Versión 20261124130000 · 24/11/2026

- Las flechas de la mesa ahora van al revés que antes: salen de la carta contestada y apuntan a la respuesta.

## Versión 20261124120000 · 24/11/2026

### 1. Mesa: quién contesta a quién (ui/app.js, función `htmlPista` y `render`)
- Cada serie de la mesa lleva un número (1, 2, 3… por combate), el mismo que en la crónica (`registrar` guarda `n` y `serie`).
- Una línea con flechas une cada respuesta con la carta que interviene: función nueva `dibujarEnlaces()`, que se llama en `render()` después de pintar la pista y al cambiar el tamaño de la ventana.
- Al pasar el ratón por una entrada de la crónica se resaltan sus cartas y su línea (`resaltarSerie`).
- CSS nuevo: `.num-serie`, `.enlaces`, `.celda.resaltada`. Las filas de la pista tienen más hueco lateral (`.pista .fila`).

### 2. Bienvenida y arranque (ui/app.js `iniciar`, HTML `#dlg-bienvenida`)
- La primera vez sale una ventana con tres ideas y los botones «Partida de aprendizaje», «Jugar ya» y «Leer Cómo jugar». Se recuerda en `localStorage` (`destreza.bienvenida`).
- Con `?bienvenida` en la dirección sale siempre.
- Arreglo: el ordenador ya no juega por detrás del menú inicial. Hasta pulsar «Empezar» la mesa está en espera (`ui.enEspera`), y «Cancelar» la deja así.

### 3. Partida de aprendizaje (ui/app.js, bloque `TUTORIAL`)
- Siempre la misma: semilla 12679, 5 de vida, empieza Blanco. El rival sigue un guion (`crearRivalTutorial`) y a la persona solo se le deja hacer la jugada del guion (`permiteTutorial`, comprobado en `comprobarSeleccion`, `respuestaSobreRival`, `alPulsarRival` y `jugar`).
- Panel con las instrucciones entre la pista y la mano (`htmlTutor`). En el móvil solo se ve la orden corta, y la explicación se abre con un botón.
- No se guarda en el Historial ni como partida en curso.
- Botón «Partida de aprendizaje» también en la ventana de Nueva partida.
- Textos en español y portugués (los del panel están en `TUTORIAL.es` / `TUTORIAL.pt`; el resto, en `FRASES_PT` de ui/pt.js).
- **Ojo:** si cambian las reglas, las cartas o el barajado, el guion puede dejar de cuadrar. Hay que volver a comprobarlo.


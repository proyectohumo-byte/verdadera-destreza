# Cambios: ranking global con Supabase (21/11/2026)

Pedido por el autor: ver quién entra al juego, cuánto juega y tener un ranking de jugadores. Nada de esta carpeta modifica el `index.html` publicado.

## Para quien vaya a aplicarlo (Claude Code)

Aplica los cambios en el **proyecto fuente**, no en el `index.html` compilado. `aplicar-red.py` solo reproduce la versión de prueba sobre el `nuevo.html` de los cambios de niveles. Confirma antes que los nombres que usa `red.js` existen en tu código: `leerJSON`, `guardarJSON`, `leerNombres`, `escapar`, `$`, `ui`, `NIVELES`, `RIVAL`, `golpesDeCronica`, `contarDobles`, `registrarResultado`, `abrirRanking`, `empezarPartida`, `iniciar`. Si algo no coincide, dilo y no lo fuerces.

## Cómo funciona

- **Base de datos** (`base-de-datos.sql`, ya ejecutado en el proyecto de Supabase del autor). Dos tablas (`jugadores`, `partidas`) sin acceso directo para la clave pública. Solo se pueden llamar tres funciones: `registrar_visita`, `registrar_partida` y `ranking_global`, que validan los datos (límites de longitud y de valores, 10 s mínimo entre dos partidas del mismo jugador).
- **Cliente** (`red.js`): bloque de código que va en `ui/app.js`. La URL y la clave `sb_publishable_...` están en la constante `RED` y son públicas por diseño. Si cambia de proyecto, solo hay que tocar esa constante.
- **Participación voluntaria**: la primera vez que se abre el juego aparece una ventana que explica qué se envía y pide un apodo; "Participar" o "No, gracias". La respuesta se guarda en `destreza.red` y no se vuelve a preguntar. Se puede cambiar el apodo o dejar de participar desde **Historial → Ranking global**. Si no participa, no se envía nada.
- **Qué se envía** (solo partidas contra el ordenador, al terminar): identificador aleatorio del navegador, apodo, nivel del rival, si ganó, tocados dados y recibidos, dobles tocados, muertes súbitas, duración en segundos y versión. Sin correo ni IP propia.
- **Sin conexión**: las partidas se guardan en `destreza.redCola` (máximo 20) y se envían, una cada 10,5 s, al volver a abrir el juego o al terminar otra partida. Un fallo de red nunca rompe el juego.
- **Ranking global**: botón en el Historial; tabla con apodo, partidas, ganadas, puntos y tocados. Puntos: cada victoria vale según el nivel vencido (Bisoño 1, Discípulo 2, Diestro 3, Preboste 4, Maestro 5). Es una propuesta: se cambia en `ranking_global()`.

## Cambios en el código (los hace `aplicar-red.py`)

1. Ventana nueva `#dlg-red` y estilos `.red-*`.
2. El bloque de `red.js`, antes de `let filtroHistorial`.
3. `registrarResultado` llama a `enviarPartidaRed(e)` al empezar.
4. `empezarPartida` guarda `ui.inicioPartida = Date.now()` (para la duración).
5. `abrirRanking` antepone `botonRed()`.
6. En el manejador de botones: `a.startsWith('red-')` llama a `accionRed(a)`.
7. `iniciar` llama a `iniciarRed()` (después de abrir "Nueva partida", para que el aviso quede encima).

## Cómo lo ve el autor

En el panel de Supabase, **Table Editor** (`jugadores` y `partidas`) o, en **SQL Editor**, la consulta comentada al final de `base-de-datos.sql`: quién entra, cuántas partidas, cuántos minutos, última vez.

## Pruebas

`prueba-red.js` (Playwright) usa una Supabase simulada y comprueba: aviso a la primera vez, participar, envío de la partida con sus datos, ranking con nombres escapados, cola sin conexión y reintento, y "No, gracias" (cero llamadas, no vuelve a preguntar). No se ha podido probar contra el Supabase real desde la sesión de Claude: el primer envío real hay que comprobarlo mirando la tabla `partidas`.

## Limitaciones conocidas

- Si se retoma una partida en curso tras recargar, la duración enviada solo cuenta desde que se retomó (`ui.inicioPartida` no se guarda con la partida en curso).
- Sin cuentas, nada impide enviar resultados falsos a mano: vale para pruebas con amigos, no para un ranking público serio.
- Las partidas jugadas antes de aceptar participar no se envían.

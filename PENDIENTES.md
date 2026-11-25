# Cosas pendientes

Ideas y tareas que quedan por hacer, por si hacen falta. Cuando se haga una, se borra de aquí y se apunta en CAMBIOS.md.

---

## Partidas con todas las cartas: «victoria media, derrota entera» (solo si hace falta)

- **Cuándo:** si en el panel del autor se ve que la gente sube de categoría demasiado rápido jugando con todas las cartas en la mano (columna «Con todas» en naranja, o un % muy alto con todas).
- **Ahora (desde el 25/11/2026):** una partida con todas las cartas cuenta como media partida, tanto si se gana como si se pierde. Así se tarda el doble en completar cada categoría, pero si alguien juega solo con todas, su % no baja (8 de 10 sigue siendo 80 %).
- **La idea:** que con todas las cartas la victoria cuente media y la derrota entera. Con 8 victorias y 2 derrotas contarían 4 victorias y 2 derrotas: 67 % en lugar de 80 %. Ganar con todas es más fácil; perder con todas no tiene excusa.
- **Dónde se cambia:** `pesoPartida` (juego: título, Historial) pasaría a depender de si se ganó; en Supabase, `ranking_global` (el 0.5 solo en las ganadas). Antes de cambiarlo, simular cuánto baja el % de quien juega solo con todas.

## Pasar el rediseño al código fuente

- El rediseño del 24/11/2026 y los cambios posteriores se hicieron directamente en este `index.html` publicado. El código fuente (`ui/`, `engine/`…) no los tiene.
- Hasta que se pasen, **no usar `npm run publicar`**: lo sobrescribiría con la versión anterior al rediseño.

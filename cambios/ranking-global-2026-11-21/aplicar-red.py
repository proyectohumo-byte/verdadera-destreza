# Añade el ranking global (Supabase) a la versión de prueba del juego.
# Uso: python3 aplicar-red.py nuevo.html red.js salida.html
import sys
entrada, modulo, salida = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(entrada, encoding='utf-8').read()
red = open(modulo, encoding='utf-8').read()

def una(viejo, nuevo):
    global s
    assert s.count(viejo) == 1, (s.count(viejo), viejo[:70])
    s = s.replace(viejo, nuevo)

# 1. Ventana del ranking global.
una('  <dialog id="dlg-reglas" class="dlg-reglas dlg-como">',
    '  <dialog id="dlg-red" class="dlg-reglas"><div id="red-contenido"></div></dialog>\n  <dialog id="dlg-reglas" class="dlg-reglas dlg-como">')
# 2. Estilos.
una('.tabla-ranking { width: 100%; border-collapse: collapse; font-size: 14px; }',
    '''.red-aviso { font-size: 13px; opacity: 0.8; }
.red-campo { display: block; margin: 8px 0; }
.red-campo input { width: 100%; box-sizing: border-box; margin-top: 4px; padding: 6px; font: inherit; }
.red-boton { margin: 4px 0 8px; }
.red-estrellas { text-align: center; margin: 8px 0; }
.red-estrella { background: none; border: 0; padding: 0 6px; font-size: 36px; line-height: 1; color: var(--sangre); cursor: pointer; }
.red-campo textarea { width: 100%; box-sizing: border-box; margin-top: 4px; padding: 6px; font: inherit; }
.tabla-ranking { width: 100%; border-collapse: collapse; font-size: 14px; }''')
# 3. Código del ranking global.
una("let filtroHistorial = 'todas';", red + "let filtroHistorial = 'todas';")
# 4. Enviar el resultado al terminar la partida.
una('function registrarResultado(e) {\n  if (!ui.nombres) return;\n',
    'function registrarResultado(e) {\n  if (!ui.nombres) return;\n  enviarPartidaRed(e);\n')
# 5. Hora de inicio de la partida (para la duración).
una('  ui.registro = [{ texto: `Nueva partida. Empieza declarando',
    '  ui.inicioPartida = Date.now();\n  ui.registro = [{ texto: `Nueva partida. Empieza declarando')
# 6. Botón en el Historial.
una("$('#ranking-contenido').innerHTML = htmlTitulos(todas)", "$('#ranking-contenido').innerHTML = botonRed() + htmlTitulos(todas)")
# 7. Acciones de los botones.
una("      else if (a === 'ranking') abrirRanking();\n",
    "      else if (a === 'ranking') abrirRanking();\n      else if (a.startsWith('red-')) accionRed(a, boton);\n")
# 8. Al arrancar.
una('  if (retomarEnCurso()) return;\n  render();\n  abrirNuevaPartida();\n',
    '  if (retomarEnCurso()) { iniciarRed(); return; }\n  render();\n  abrirNuevaPartida();\n  iniciarRed();\n')
open(salida, 'w', encoding='utf-8').write(s)
print('ok', len(s))

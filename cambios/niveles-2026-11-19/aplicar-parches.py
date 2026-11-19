# Aplica los parches A-D al index.html compilado (solo para reproducir la versión de prueba).
# Uso: python3 aplicar-parches.py index.html niveles.js salida.html
import sys
entrada, modulo, salida = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(entrada, encoding='utf-8').read()
niv = open(modulo, encoding='utf-8').read()
marca = '// ---- ui/datos.js ----'
assert s.count(marca) == 1
s = s.replace(marca, niv + marca)
viejo = '''        <label><input type="radio" name="nivel" value="reglas" checked> Normal: elige la mejor jugada según reglas fijas</label>
        <label><input type="radio" name="nivel" value="azar"> Fácil: juega cualquier jugada legal al azar</label>'''
assert s.count(viejo) == 1
nuevo = '''        <label><input type="radio" name="nivel" value="bisono"> <b>Bisoño</b>: apenas sabe jugar; se despista mucho</label>
        <label><input type="radio" name="nivel" value="discipulo"> <b>Discípulo</b>: piensa en el daño inmediato y no recuerda lo que has jugado</label>
        <label><input type="radio" name="nivel" value="diestro" checked> <b>Diestro</b>: recuerda tus últimas jugadas, aunque a veces falla</label>
        <label><input type="radio" name="nivel" value="preboste"> <b>Preboste</b>: ayudante del maestro; lleva la cuenta de las cartas con cierta fiabilidad</label>
        <label><input type="radio" name="nivel" value="maestro"> <b>Maestro</b>: casi no olvida nada, aunque no ve tu mano ni es perfecto</label>'''
s = s.replace(viejo, nuevo)
v1 = "ui.rival = f.get('nivel') === 'azar' ? crearRivalAzar() : crearRivalReglas();"
assert s.count(v1) == 1
s = s.replace(v1, "ui.rival = crearRivalNivel(f.get('nivel'));")
v2 = "(f.get('nivel') === 'azar' ? 'Ordenador (fácil)' : 'Ordenador (normal)')"
assert s.count(v2) == 1
s = s.replace(v2, "`Ordenador (${nivelPorId(f.get('nivel')).nombre.toLowerCase()})`")
v3 = "  ui.rival = crearRivalReglas();\n  $('#defs')"
assert s.count(v3) == 1
s = s.replace(v3, "  ui.rival = crearRivalNivel(NIVEL_POR_DEFECTO);\n  $('#defs')")
open(salida, 'w', encoding='utf-8').write(s)
print('ok', len(s))

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
nuevo = '''        <label><input type="radio" name="nivel" value="bisono"> <b>Bisoño</b>: Mozo recién llegado a la sala de armas: empuña la espada con respeto, pero poco sabe de ella.</label>
        <label><input type="radio" name="nivel" value="discipulo"> <b>Discípulo</b>: Aprende el compás bajo la vista del maestro: atiende a la estocada que tiene delante, no a la que vendrá.</label>
        <label><input type="radio" name="nivel" value="diestro" checked> <b>Diestro</b>: Hombre ya ducho en la ciencia de las armas: guarda memoria de tus últimas jugadas, aunque la memoria a veces le falla.</label>
        <label><input type="radio" name="nivel" value="preboste"> <b>Preboste</b>: Ayudante del maestro, con licencia para enseñar en su ausencia: lleva buena cuenta de las cartas, sin llegar a la certeza.</label>
        <label><input type="radio" name="nivel" value="maestro"> <b>Maestro</b>: Examinado en el arte y respetado en la plaza: casi nada se le escapa, pero ni ve tu mano ni es infalible.</label>'''
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
v5 = "const primera = ci === 0 && esDeclarada ? `<span class=\"suma-serie\">suma ${danoPendiente(e).suma}</span>` : '';"
assert s.count(v5) == 1
n5 = "const dp = danoPendiente(e);\n        const primera = ci === 0 && esDeclarada ? `<span class=\"suma-serie\" title=\"${dp.suma} de la serie${dp.mas1 ? ' + 1 por contestar una carta del rival' : ' (sin +1: abre el combate)'}${dp.extra ? ' + ' + dp.extra + ' por la apertura cercana rival' : ''}\">suma ${dp.dano}</span>` : '';"
s = s.replace(v5, n5)
open(salida, 'w', encoding='utf-8').write(s)
print('ok', len(s))

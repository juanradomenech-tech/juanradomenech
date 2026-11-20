"""Actualiza las cifras de Strava de la web a partir de las actividades nuevas.

Uso:  python3 actualizar_strava.py nuevas.json
  nuevas.json = lista de actividades tal como las devuelve el conector de Strava
  (list_activities con range_start = "hasta" de strava_resumen.json).
Suma solo las de bici que no estén ya contadas, actualiza strava_resumen.json y
contenido.json (cifras, notas, últimas salidas y texto del asistente).
Imprime CAMBIOS=1 si hay algo nuevo, CAMBIOS=0 si no.
"""
import json, re, sys, datetime as dt
from pathlib import Path

BICI = {'Ride', 'VirtualRide', 'MountainBikeRide', 'GravelRide', 'EBikeRide', 'EMountainBikeRide', 'Velomobile', 'Handcycle'}
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
MES_CORTO = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sept', 'oct', 'nov', 'dic']
EVEREST = 8849

base = Path(__file__).parent
res_p, cont_p = base / 'strava_resumen.json', base / 'contenido.json'
res = json.loads(res_p.read_text())
data = json.loads(Path(sys.argv[1]).read_text())
acts = data['activities'] if isinstance(data, dict) else data

def miles(n):
    return f"{n:,}".replace(',', '.')

def dec(x):
    return f"{x:.1f}".replace('.', ',')

def duracion(seg):
    m = round(seg / 60)
    return f"{m // 60} h {m % 60} min" if m >= 60 else f"{m} min"

nuevas = []
for a in sorted(acts, key=lambda a: a['start_local']):
    if a.get('sport_type') not in BICI:
        continue
    fecha = a['start_local']
    anio = int(fecha[:4])
    if anio != res['anio']:
        if anio < res['anio']:
            continue
        # Año nuevo: se empieza de cero
        res.update(anio=anio, metros=0, segundos=0, desnivel=0, salidas=0, hasta=f"{anio}-01-01T00:00:00", ids_contados_ultimo_dia=[])
    if fecha < res['hasta'] or a['id'] in res['ids_contados_ultimo_dia']:
        continue
    s = a['summary']
    res['metros'] += s.get('distance') or 0
    res['segundos'] += s.get('moving_time') or 0
    res['desnivel'] += round(s.get('elevation_gain') or 0)
    res['salidas'] += 1
    if fecha[:10] != res['hasta'][:10]:
        res['ids_contados_ultimo_dia'] = []
    res['ids_contados_ultimo_dia'].append(a['id'])
    res['hasta'] = fecha
    nuevas.append(a)

if not nuevas:
    print('CAMBIOS=0')
    sys.exit(0)

c = json.loads(cont_p.read_text())
z = c['ciclista']
km, h, des = round(res['metros'] / 1000), round(res['segundos'] / 3600), res['desnivel']
y = res['anio']
z['cifras'][0].update(numero=miles(km), texto=f"recorridos en {y}")
z['cifras'][1].update(numero=miles(des), texto=f"de desnivel positivo: más de {des // EVEREST} veces el Everest")
z['cifras'][2]['numero'] = miles(res['salidas'])
z['cifras'][3].update(numero=miles(h), texto=f"pedaleando en {y}")
hoy = dt.date.today()
ultima = dt.date.fromisoformat(res['hasta'][:10])
z['cifras_nota'] = f"Datos de Strava del 1 de enero al {ultima.day} de {MESES[ultima.month - 1]} de {y}."
z['datos_strava'] = f"Fuente: Strava, consultado el {hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}."

fichas = []
for a in reversed(nuevas):
    s, d = a['summary'], dt.date.fromisoformat(a['start_local'][:10])
    fichas.append({
        'fecha': f"{d.day} {MES_CORTO[d.month - 1]} {d.year}",
        'nombre': a['name'],
        'km': dec((s.get('distance') or 0) / 1000),
        'desnivel': miles(round(s.get('elevation_gain') or 0)),
        'tiempo': duracion(s.get('moving_time') or 0),
        'velocidad': dec((s.get('avg_speed') or 0) * 3.6),
        'url': f"https://www.strava.com/activities/{a['id']}",
    })
n = len(z['ultimas']) or 3
vistos = {f['url'] for f in fichas}
z['ultimas'] = (fichas + [u for u in z['ultimas'] if u['url'] not in vistos])[:n]

txt = json.dumps(c, ensure_ascii=False, indent=2)
txt = re.sub(r"En \d{4} llevo [\d.]+ km y [\d.]+ m de desnivel", f"En {y} llevo {miles(km)} km y {miles(des)} m de desnivel", txt)
cont_p.write_text(txt)
res_p.write_text(json.dumps(res, ensure_ascii=False, indent=2))
print(f"CAMBIOS=1 · {len(nuevas)} salida(s) nueva(s) · {miles(km)} km · {miles(des)} m · {res['salidas']} salidas · {h} h")

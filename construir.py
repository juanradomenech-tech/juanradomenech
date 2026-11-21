#!/usr/bin/env python3
"""Genera la web de juanradomenech.com en la carpeta publicar/.

Uso:  python3 construir.py
Lee contenido.json, copia recursos/ y media/, y escribe las páginas.
Solo usa la biblioteca estándar de Python.
"""
import html
import json
import math
import random
import re
import shutil
import sys
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent
SALIDA = BASE / "publicar"
C = json.loads((BASE / "contenido.json").read_text(encoding="utf-8"))
HOY = date.today()
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
FECHA = f"{HOY.day} de {MESES[HOY.month - 1]} de {HOY.year}"


def e(t):
    return html.escape(str(t), quote=True)


def lleno(v):
    return v is not None and str(v).strip() != ""


# ---------------------------------------------------------------- grafismos
_N = 0

def arte_reticula(semilla, clase="arte"):
    """Retícula fina con nodos naranjas: el grafismo de la parte de consultor."""
    r = random.Random(semilla)
    w, h, paso = 600, 900, 60
    lineas = []
    for x in range(0, w + 1, paso):
        lineas.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{h}"/>')
    for y in range(0, h + 1, paso):
        lineas.append(f'<line x1="0" y1="{y}" x2="{w}" y2="{y}"/>')
    # un camino que recorre la retícula
    x, y = r.randrange(1, 4) * paso, h - paso * 2
    puntos = [(x, y)]
    for _ in range(9):
        if r.random() < .55:
            y -= paso * r.randint(1, 3)
        else:
            x = min(w - paso, max(paso, x + paso * r.choice([-2, -1, 1, 2])))
        puntos.append((x, max(paso, y)))
    camino = " ".join(f"{px},{py}" for px, py in puntos)
    nodos = "".join(f'<circle cx="{px}" cy="{py}" r="4"/>' for px, py in puntos[1:-1])
    fin = puntos[-1]
    return (f'<svg class="{clase}" viewBox="0 0 {w} {h}" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">'
            f'<g stroke="#FFFFFF" stroke-opacity=".08" stroke-width="1">{"".join(lineas)}</g>'
            f'<polyline points="{camino}" fill="none" stroke="#FF671F" stroke-width="2" stroke-opacity=".9"/>'
            f'<g fill="#FF671F">{nodos}</g>'
            f'<circle cx="{fin[0]}" cy="{fin[1]}" r="10" fill="none" stroke="#FF671F" stroke-width="2"/>'
            f'<circle cx="{fin[0]}" cy="{fin[1]}" r="4" fill="#FFFFFF"/></svg>')


def decodificar_polyline(cad):
    pts, i, lat, lng = [], 0, 0, 0
    while i < len(cad):
        vals = []
        for _ in range(2):
            res, sh = 0, 0
            while True:
                b = ord(cad[i]) - 63; i += 1
                res |= (b & 0x1f) << sh; sh += 5
                if b < 0x20:
                    break
            vals.append(~(res >> 1) if res & 1 else res >> 1)
        lat += vals[0]; lng += vals[1]
        pts.append((lat / 1e5, lng / 1e5))
    return pts


def arte_ruta(poly, clase="arte-ruta"):
    """Silueta real de la ruta (GPS de Strava) proyectada en la mitad superior de la tarjeta."""
    pts = decodificar_polyline(poly)
    if len(pts) < 2:
        return ""
    lat0 = sum(p[0] for p in pts) / len(pts)
    k = math.cos(math.radians(lat0))
    xy = [(p[1] * k, -p[0]) for p in pts]
    x0, x1 = min(p[0] for p in xy), max(p[0] for p in xy)
    y0, y1 = min(p[1] for p in xy), max(p[1] for p in xy)
    esc = 560 / max((x1 - x0), (y1 - y0) * 2, 1e-9)   # escala común, rutas anchas o altas
    q = [((x - x0) * esc, (y - y0) * esc) for x, y in xy]
    an, al = (x1 - x0) * esc, (y1 - y0) * esc
    pad = 18
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in q)
    (sx, sy), (fx, fy) = q[0], q[-1]
    vb = f"{-pad:.1f} {-pad:.1f} {an + 2 * pad:.1f} {al + 2 * pad:.1f}"
    rp = max(an + 2 * pad, (al + 2 * pad) * 1.6) * 0.011   # puntos del mismo tamaño en todas las tarjetas
    return f'''<svg class="{clase}" viewBox="{vb}" preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false">
  <path d="{d}" class="ruta-sombra"/>
  <path d="{d}" class="ruta-linea"/>
  <circle cx="{sx:.1f}" cy="{sy:.1f}" r="{rp * 1.3:.1f}" class="ruta-inicio"/>
  {f'<circle cx="{fx:.1f}" cy="{fy:.1f}" r="{rp:.1f}" class="ruta-fin"/>' if abs(fx - sx) + abs(fy - sy) > rp * 3 else ""}
</svg>'''


def arte_curvas():
    """Carretera de montaña en zigzag (curvas de herradura), de abajo arriba."""
    pts, y, izq = [], 640, True
    d = "M 120 680 L 120 640"
    for k in range(6):
        x1, x2 = (120, 480) if izq else (480, 120)
        y2 = y - 95
        d += f" L {x2 - (30 if izq else -30)} {y - 10} Q {x2 + (40 if izq else -40)} {y - 47} {x2 - (30 if izq else -30)} {y2}"
        pts.append((x2, y - 47))
        y, izq = y2, not izq
    km = "".join(f'<circle cx="{x + (55 if x > 300 else -55)}" cy="{yy}" r="4" class="curva-hito"/>' for x, yy in pts)
    return f'''<svg class="arte-curvas" viewBox="0 0 600 720" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">
  <path d="{d}" class="curva-asfalto"/>
  <path d="{d}" class="curva-linea"/>
  {km}
  <circle cx="120" cy="680" r="9" class="curva-inicio"/>
  <g transform="translate({pts[-1][0] - 30 if pts[-1][0] > 300 else pts[-1][0] + 30} {y})"><circle r="11" class="curva-meta"/><path d="M -2 -30 L -2 -6 M -2 -30 L 18 -23 L -2 -16" class="curva-bandera"/></g>
  <text x="140" y="700" class="curva-txt">HOY</text>
  <text x="300" y="{y - 40}" class="curva-txt" text-anchor="middle">FRANCIA 2027</text>
</svg>'''


def arte_altimetria(semilla, clase="arte", alto=900):
    """Perfil de altimetría de un puerto: el grafismo de la parte de ciclista."""
    r = random.Random(semilla)
    w, h = 600, alto
    base = h * .78
    n = 60
    ys = []
    nivel = 0.0
    for i in range(n + 1):
        t = i / n
        nivel += r.uniform(-.004, .03) + .01 * math.sin(t * 6 + semilla)
        ys.append(nivel)
    mx = max(ys) or 1
    pts = []
    for i, v in enumerate(ys):
        px = w * i / n
        py = base - (v / mx) * h * .5
        pts.append((round(px, 1), round(py, 1)))
    perfil = " ".join(f"{x},{y}" for x, y in pts)
    relleno = f"0,{h} " + perfil + f" {w},{h}"
    global _N
    _N += 1
    gid = f"alt{_N}"
    marcas = "".join(
        f'<line x1="{w * k / 6:.0f}" y1="{base + 14}" x2="{w * k / 6:.0f}" y2="{base + 24}"/>' for k in range(1, 6))
    cima = max(pts, key=lambda p: -p[1])
    return (f'<svg class="{clase}" viewBox="0 0 {w} {h}" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">'
            f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="#FF671F" stop-opacity=".45"/><stop offset="1" stop-color="#FF671F" stop-opacity="0"/>'
            f'</linearGradient></defs>'
            f'<g stroke="#FFFFFF" stroke-opacity=".07">'
            + "".join(f'<line x1="0" y1="{y}" x2="{w}" y2="{y}"/>' for y in range(60, h, 90)) +
            f'</g><polygon points="{relleno}" fill="url(#{gid})"/>'
            f'<polyline points="{perfil}" fill="none" stroke="#FF671F" stroke-width="2.5"/>'
            f'<g stroke="#FFFFFF" stroke-opacity=".35">{marcas}</g>'
            f'<line x1="{cima[0]}" y1="{cima[1] - 60}" x2="{cima[0]}" y2="{cima[1]}" stroke="#FFFFFF" stroke-opacity=".6"/>'
            f'<circle cx="{cima[0]}" cy="{cima[1]}" r="5" fill="#FFFFFF"/></svg>')


# ---------------------------------------------------------------- piezas
GA = (C.get("analitica", {}).get("ga4_id") or "").strip()


def scripts():
    extra = '\n<script src="/js/consentimiento.js" defer></script>' if GA else ""
    return '<script src="/js/web.js" defer></script>' + extra


def asistente_html():
    a = C.get("asistente") or {}
    if not a.get("mostrar"):
        return ""
    datos = {k: a.get(k) for k in ("saludo", "inicio", "temas", "no_entiendo", "correo_asunto")}
    datos["correo"] = C["contacto"].get("correo", "")
    datos["agenda"] = C["contacto"].get("agenda_url", "")
    js = json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")
    foto = f'<img src="{e(a["foto"])}" alt="" width="40" height="40">' if lleno(a.get("foto")) else "<b>JD</b>"
    ico = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M4 4h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H9l-5 4v-4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zm3 6.5a1.5 1.5 0 1 0 0 .01zm5 0a1.5 1.5 0 1 0 0 .01zm5 0a1.5 1.5 0 1 0 0 .01z"/></svg>'
    env = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M3 20.5 21 12 3 3.5 3 10l12 2-12 2z"/></svg>'
    return f'''<div class="bot">
  <script type="application/json" id="bot-datos">{js}</script>
  <div class="bot-panel" id="bot-panel" role="dialog" aria-label="{e(a.get("nombre", "Asistente"))}" hidden>
    <div class="bot-cab">{foto}<div><strong>{e(a.get("nombre", "Asistente"))}</strong><span>{e(a.get("estado", ""))}</span></div>
      <button type="button" class="bot-cerrar" aria-label="Cerrar">×</button></div>
    <div class="bot-msgs" aria-live="polite"></div>
    <form class="bot-form"><label class="sr-only" for="bot-texto">Tu pregunta</label>
      <input id="bot-texto" type="text" autocomplete="off" placeholder="Escribe tu pregunta…">
      <button type="submit" class="bot-enviar" aria-label="Enviar">{env}</button></form>
  </div>
  <button type="button" class="bot-boton" aria-expanded="false" aria-controls="bot-panel">{ico}<span>Pregúntame</span></button>
</div>'''


def redes(activa=""):
    c = C["contacto"]
    items = [("LinkedIn", c.get("linkedin")), ("Instagram", c.get("instagram")), ("Strava", c.get("strava"))]
    # En la página profesional no sale Strava; en Ciclista no sale LinkedIn
    quitar = {"consultor": "Strava", "ciclista": "LinkedIn"}.get(activa)
    items = [(n, u) for n, u in items if n != quitar]
    return "".join(f'<a href="{e(u)}" target="_blank" rel="noopener me">{n}</a>' for n, u in items if lleno(u))


def cabecera(activa=""):
    def enlace(href, texto, clave):
        actual = ' class="activo" aria-current="page"' if clave == activa else ""
        return f'<a href="{href}"{actual}>{texto}</a>'
    menu = (enlace("/consultor.html", C["consultor"].get("rol", "Consultor"), "consultor") + enlace("/ciclista.html", "Ciclista", "ciclista")
            + '<a href="#contacto">Contacto</a>'
            + "".join(enlace("/" + ap["ruta"], ap["menu"], k) for k, ap in C.get("apps", {}).items()
                      if ap.get("publicar") and lleno(ap.get("menu"))))
    return f'''<a class="saltar" href="#contenido">Saltar al contenido</a>
<header class="cabecera">
  <a class="logo" href="/" aria-label="Juanra Doménech, inicio"><svg class="logo-bola" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><defs><radialGradient id="bola8" cx="34%" cy="28%" r="78%"><stop offset="0" stop-color="#5a5a5a"/><stop offset=".45" stop-color="#161616"/><stop offset="1" stop-color="#000"/></radialGradient></defs><circle cx="16" cy="16" r="15.2" fill="url(#bola8)" stroke="rgba(255,255,255,.28)" stroke-width=".8"/><circle cx="14.6" cy="13.6" r="6.6" fill="#f4f4f4"/><text x="14.6" y="17.1" text-anchor="middle" font-family="Barlow Condensed, Arial, sans-serif" font-weight="800" font-size="10" fill="#000">8</text><ellipse cx="9.2" cy="7.6" rx="3.2" ry="1.7" fill="#fff" opacity=".35" transform="rotate(-30 9.2 7.6)"/></svg><span class="logo-nombre">Juanra <span>Doménech</span></span></a>
  <nav class="menu" aria-label="Principal">{menu}</nav>
  <button class="menu-boton" type="button" aria-label="Abrir el menú" aria-expanded="false" aria-controls="menu-movil"><span></span><span></span><span></span></button>
</header>
<div class="menu-movil" id="menu-movil">
  <a href="/">Inicio</a>{menu}
  <div class="menu-pie"><a href="/aviso-legal.html">Aviso legal</a><a href="/privacidad.html">Privacidad</a>{redes()}</div>
</div>'''


def telefono_html(clase):
    tel = C["contacto"].get("telefono", "")
    if not lleno(tel):
        return ""
    return f'<p class="{clase}">Teléfono profesional <a href="tel:+34{e(tel.replace(" ", ""))}">{e(tel)}</a></p>'


def pie(activa=""):
    return f'''<footer class="pie">
  <span>© {HOY.year} Juanra Doménech{f' · <a href="tel:+34{e(C["contacto"]["telefono"].replace(" ", ""))}">{e(C["contacto"]["telefono"])}</a>' if lleno(C["contacto"].get("telefono")) and activa == "consultor" else ""}</span>
  <nav aria-label="Legal"><a href="/aviso-legal.html">Aviso legal</a><a href="/privacidad.html">Privacidad</a><a href="/cookies.html">Cookies</a>{'<button type="button" class="pie-cookies" data-cookies hidden>Configurar cookies</button>' if GA else ""}</nav>
</footer>'''


def head(titulo, descripcion, ruta="/", indexar=True):
    s = C["sitio"]
    url = s["dominio"].rstrip("/") + ruta
    robots = "" if indexar else '<meta name="robots" content="noindex">'
    return f'''<!DOCTYPE html>
<html lang="es"{f' data-ga="{e(GA)}"' if GA else ""}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descripcion)}">
{robots}
<link rel="canonical" href="{e(url)}">
<meta name="theme-color" content="#000000">
<meta property="og:type" content="website">
<meta property="og:locale" content="es_ES">
<meta property="og:site_name" content="{e(s['nombre'])}">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(descripcion)}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{e(s['dominio'].rstrip('/'))}/img/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/img/apple-touch-icon.png">
<link rel="preload" href="/fonts/barlow-condensed-latin-700-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/figtree-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/css/estilos.css">
'''


def cifras_html(lista, clase="cifras"):
    vis = [c for c in lista if lleno(c.get("numero"))]
    if not vis:
        return ""
    extra = " cifras--3" if len(vis) == 3 else ""
    return f'<div class="{clase}{extra} aparece">' + "".join(
        f'<div class="cifra"><b>{e(c["numero"])}<small>{e(c.get("sufijo", ""))}</small></b><span>{e(c["texto"])}</span></div>'
        for c in vis) + "</div>"


def carrusel(id_, etiqueta, tarjetas_html):
    return f'''<div class="carrusel aparece" id="{id_}">
  <div class="pista" tabindex="0" role="region" aria-roledescription="carrusel" aria-label="{e(etiqueta)}">{tarjetas_html}</div>
  <div class="wrap controles">
    <div class="puntos" aria-label="Elegir tarjeta"></div>
    <div class="flechas"><button type="button" data-ant aria-label="Anterior">←</button><button type="button" data-sig aria-label="Siguiente">→</button></div>
  </div>
</div>'''


# ---------------------------------------------------------------- páginas
def panel(clave, num, arte, destino, etiqueta="h2", clase="panel"):
    d = C["portada"][clave]
    foto = d.get("foto", "")
    fondo = (f'<img class="foto foto--{clave}" src="/{e(foto)}" alt="" loading="eager">'
             if lleno(foto) and (BASE / foto).exists() else arte)
    return f'''<a class="{clase}" href="{destino}">
    {fondo}
    <span class="panel-num">{num}</span>
    <div class="panel-texto">
      <{etiqueta}>{e(d["titulo"])}<span>{e(d["subtitulo"])}</span></{etiqueta}>
      <p>{e(d["frase"])}</p>
      <span class="ver-mas">Ver más <i>→</i></span>
    </div>
  </a>'''


def portada_pagina(clave, num, arte, foto=""):
    d = C["portada"][clave]
    fondo = (f'<img class="foto foto--cabecera" src="/{e(foto)}" alt="" fetchpriority="high">'
             if lleno(foto) and (BASE / foto).exists() else arte)
    return f'''<section class="portada portada--pagina" aria-labelledby="t-{clave}">
  <div class="panel panel--fijo">
    {fondo}
    <span class="panel-num">{num}</span>
    <div class="panel-texto">
      <h1 id="t-{clave}">{e(d["titulo"])}<span>{e(d["subtitulo"])}</span></h1>
      <p>{e(d["frase"])}</p>
    </div>
  </div>
</section>'''


def otra_mitad(clave, num, arte, destino):
    return f'''<section class="otra-mitad" aria-label="La otra mitad">
  <span class="etiqueta otra-etiqueta">La otra mitad</span>
  {panel(clave, num, arte, destino)}
</section>'''


def puente_html():
    pu = C["puente"]
    ideas = "".join(f'<div class="idea"><h3>{e(i["titulo"])}</h3><p>{e(i["texto"])}</p></div>' for i in pu["ideas"])
    return f'''<section class="puente" aria-labelledby="t-puente">
  {arte_altimetria(3, "arte-puente", 400)}
  <div class="wrap">
    <span class="etiqueta">{e(C["consultor"].get("rol", "Consultor"))} + Ciclista</span>
    <h2 class="titulo aparece" id="t-puente">{e(pu["titulo"])}</h2>
    <p class="entradilla aparece">{e(pu["entradilla"])}</p>
    <div class="ideas aparece">{ideas}</div>
  </div>
</section>'''


def tiempo_entradilla(t):
    txt, dst = t["entradilla"], t.get("destacado") or ""
    if not dst or dst not in txt:
        return f'<p class="entradilla aparece">{e(txt)}</p>'
    antes, despues = (x.strip() for x in txt.split(dst, 1))
    return (f'<p class="entradilla aparece">{e(antes)}</p>'
            f'<p class="tiempo-destacado aparece"><span>{e(dst)}</span></p>'
            + (f'<p class="entradilla tiempo-despues aparece">{e(despues)}</p>' if despues else ""))


def tiempo_html():
    t = C.get("tiempo")
    if not t:
        return ""
    pasos = "".join(f'''<li class="paso"><span class="paso-n">{i:02d}</span><h3>{e(p["titulo"])}</h3><p>{e(p["texto"])}</p></li>'''
                    for i, p in enumerate(t["pasos"], 1))
    return f'''<section class="parte tiempo" aria-labelledby="t-tiempo">
  <div class="wrap">
    <span class="etiqueta">{e(t["etiqueta"])}</span>
    <figure class="cita-seneca aparece">
      <blockquote id="t-tiempo"><p>«{e(t["cita"])}»</p></blockquote>
      <figcaption><b>{e(t["autor"])}</b> · <cite>{e(t["obra"])}</cite></figcaption>
    </figure>
    {tiempo_entradilla(t)}
    <ol class="ciclo aparece">{pasos}</ol>
    <p class="ciclo-vuelta aparece" aria-hidden="true">↻ Y vuelta a empezar</p>
    <p class="tiempo-cierre aparece">{e(t["cierre"])}</p>
  </div>
</section>'''


def contacto_html(activa=""):
    cie = C["cierre"]
    mail = C["contacto"].get("correo", "")
    acciones = []
    ag = C["contacto"].get("agenda_url", "")
    if lleno(ag):
        acciones.append(f'<a class="boton boton--lg" href="{e(ag)}" target="_blank" rel="noopener">{e(C["contacto"].get("agenda_texto", "Reserva una reunión"))}</a>')
    if lleno(mail):
        acciones.append(f'<a class="boton boton--lg{" boton--linea" if acciones else ""}" href="mailto:{e(mail)}">Escríbeme</a>')
    if lleno(C["contacto"].get("linkedin")):
        clase = "boton boton--lg" + (" boton--linea" if acciones else "")
        acciones.append(f'<a class="{clase}" href="{e(C["contacto"]["linkedin"])}" target="_blank" rel="noopener">Hablemos en LinkedIn</a>')
    fondo, clase = "", "cierre"
    vid = C["ciclista"].get("video_contacto", {}) if activa == "ciclista" else {}
    if lleno(vid.get("mp4")) and (BASE / vid["mp4"]).exists():
        poster = vid.get("poster", "")
        fondo = (f'''<div class="cierre-fondo" aria-hidden="true">
    <img class="cierre-poster" src="/{e(poster)}" alt="" loading="lazy">
    <video class="cierre-video" autoplay muted loop playsinline preload="metadata" poster="/{e(poster)}"><source src="/{e(vid["mp4"])}" type="video/mp4"></video>
  </div>
  <button class="cierre-sonido" type="button" aria-pressed="false"><span class="cierre-sonido-icono" aria-hidden="true"></span><span class="cierre-sonido-texto">Activar sonido</span></button>''')
        clase = "cierre cierre--video"
    return f'''<section class="{clase}" id="contacto" aria-labelledby="t-contacto">
  {fondo}
  <div class="wrap">
    <span class="etiqueta">Contacto</span>
    <h2 class="titulo" id="t-contacto">{e(cie["titulo"])}</h2>
    <p>{e(cie["texto"])}</p>
    <div class="acciones">{"".join(acciones)}</div>
    {telefono_html("cierre-telefono") if activa == "consultor" else ""}
    <div class="redes">{redes(activa)}</div>
  </div>
</section>'''


def cuerpo(activa, contenido):
    return f'''</head>
<body>
{cabecera(activa)}
<main id="contenido">
{contenido}
{contacto_html(activa)}
</main>
{pie(activa)}
{asistente_html()}
{scripts()}
</body>
</html>
'''


def index():
    s = C["sitio"]
    persona = {
        "@context": "https://schema.org", "@type": "Person", "name": s["nombre"],
        "url": s["dominio"], "jobTitle": "AI Officer para pymes",
        **({"worksFor": {"@type": "Organization", "name": "iLumya", "url": C["consultor"]["ilumya"]["url"]}}
           if C["consultor"].get("ilumya", {}).get("mostrar") else {}),
        "description": s["descripcion"],
        "knowsAbout": ["Diseño de producto", "Inteligencia artificial", "Software", "Transformación digital", "Ciclismo"],
        **({"worksFor": {"@type": "Organization", "name": "iLumya Technologies", "url": C["consultor"]["ilumya"]["url"]},
            "jobTitle": C["consultor"]["titulo"] + " · Fundador de iLumya"} if C["consultor"].get("ilumya", {}).get("mostrar") else {}),
        "sameAs": [u for u in (C["contacto"].get(k) for k in ("linkedin", "instagram", "strava")) if lleno(u)],
    }
    contenido = f'''<section class="portada" id="inicio" aria-label="Dos partes: consultor y ciclista">
  <h1 class="sr-only">Juanra Doménech, {e(C["consultor"]["titulo"])} y ciclista</h1>
  {panel("consultor", "01", arte_reticula(7), "/consultor.html")}
  {panel("ciclista", "02", arte_altimetria(11), "/ciclista.html")}
</section>
{puente_html()}
{tiempo_html()}'''
    return (head(s["titulo"], s["descripcion"])
            + f'<script type="application/ld+json">{json.dumps(persona, ensure_ascii=False)}</script>\n'
            + cuerpo("", contenido))


def servicios_html(co):
    fams = co.get("familias", [])
    if not fams:
        return ""
    notas = "".join(f"<li>{e(n)}</li>" for n in co.get("servicios_notas", []))

    def item(sv):
        dur = sv.get("chips", [""])[0]
        return f'''<li><span class="svc-n">{e(sv["n"])}</span><div><h4>{e(sv["titulo"])}</h4>
          <p>{e(sv["frase"])}</p>{f'<i>{e(dur)}</i>' if lleno(dur) else ""}</div></li>'''

    tarjetas = "".join(f'''<div class="fam-card aparece">
      <span class="fam-et">{e(f["nombre"])}</span><h3>{e(f["pregunta"])}</h3>
      <ul class="fam-svcs">{"".join(item(x) for x in f["servicios"])}</ul>
    </div>''' for f in fams)
    return f'''<section class="parte parte--suave servicios-sec" id="servicios" aria-labelledby="t-servicios">
  <div class="wrap">
    <span class="etiqueta">Servicios</span>
    <h2 class="titulo aparece" id="t-servicios">{e(co.get("servicios_titulo", "Servicios"))}</h2>
    <p class="entradilla aparece">{e(co.get("servicios_intro", ""))}</p>
    <div class="fam-grid">{tarjetas}</div>
    {f'<ul class="encaje">{notas}</ul>' if notas else ""}
    <p class="svc-cta aparece">{(f'<a class="boton" href="{e(C["contacto"]["agenda_url"])}" target="_blank" rel="noopener">Reserva una reunión</a> ' if lleno(C["contacto"].get("agenda_url")) else "")}<a class="boton{" boton--linea" if lleno(C["contacto"].get("agenda_url")) else ""}" href="#contacto">Hablemos de tu caso</a></p>
  </div>
</section>'''


def linkedin_html(co):
    posts = [p for p in co.get("linkedin_posts", []) if lleno(p.get("texto"))]
    if not posts:
        return ""
    tarjetas = "".join(f'''<a class="post aparece" href="{e(p["url"])}" target="_blank" rel="noopener">
      <span class="salida-fecha">{e(p.get("fecha", ""))}</span>
      <p class="post-texto">{e(p["texto"])}</p>
      {f'<p class="post-datos">{e(p["datos"])}</p>' if lleno(p.get("datos")) else ""}
      <span class="ver-mas">Ver en LinkedIn <i>↗</i></span>
    </a>''' for p in posts[:3])
    li = C["contacto"].get("linkedin", "")
    boton = (f'<a class="boton boton--linea" href="{e(li)}" target="_blank" rel="noopener">Sígueme en LinkedIn</a>' if lleno(li) else "")
    return f'''<section class="parte linkedin-sec" aria-labelledby="t-linkedin">
  <div class="wrap">
    <div class="cabeza-sec cabeza-sec--primera"><div><span class="etiqueta">LinkedIn</span><h2 class="titulo-sec" id="t-linkedin">{e(co.get("linkedin_titulo", "Últimas publicaciones"))}</h2></div>{boton}</div>
    <div class="salidas">{tarjetas}</div>
    {f'<p class="fuente">{e(co["linkedin_fuente"])}</p>' if lleno(co.get("linkedin_fuente")) else ""}
  </div>
</section>'''


def metodo_html(co):
    m = co.get("metodo")
    if not m:
        return ""
    pasos = "".join(f'''<li class="met-paso aparece"><span class="met-num">{i:02d}</span><h3>{e(p["titulo"])}</h3><p>{e(p["texto"])}</p>
      <p class="met-entrega"><strong>Te llevas</strong>{e(p["entregable"])}</p></li>''' for i, p in enumerate(m["pasos"], 1))
    return f'''<section class="parte parte--suave metodo" id="metodo" aria-labelledby="t-metodo">
  <div class="wrap">
    <span class="etiqueta">Cómo trabajo</span>
    <h2 class="titulo aparece" id="t-metodo">{e(m["titulo"])}</h2>
    <p class="entradilla aparece">{e(m["intro"])}</p>
    <ol class="met-pasos">{pasos}</ol>
  </div>
</section>'''


def piramide_html(co):
    pi = co.get("piramide")
    if not pi:
        return ""
    capas = "".join(f'''<div class="pir-capa pir-capa--{i}"><strong>{e(c["texto"])}</strong><span>{e(c["detalle"])}</span></div>'''
                    for i, c in enumerate(pi["capas"], 1))
    ventajas = "".join(f'<div class="idea"><h3>{e(v["titulo"])}</h3><p>{e(v["texto"])}</p></div>' for v in pi["ventajas"])
    return f'''<section class="parte piramide-sec" id="piramide" aria-labelledby="t-piramide">
  <div class="wrap">
    <div class="pir">
      <div>
        <span class="etiqueta">Cómo está montado</span>
        <h2 class="titulo aparece" id="t-piramide">{e(pi["titulo"])}</h2>
        <p class="entradilla aparece">{e(pi["intro"])}</p>
      </div>
      <div class="pir-figura aparece" role="img" aria-label="Pirámide invertida: arriba la experiencia, en medio el diseño y la dirección, abajo la IA">{capas}</div>
    </div>
    <div class="ideas pir-ventajas aparece">{ventajas}</div>
  </div>
</section>'''


def comparativa_rol_html(co):
    cr = co.get("comparativa_rol")
    if not cr:
        return ""
    cols = "".join(f'''<div class="rol-col{" rol-col--yo" if c.get("destacada") else ""} aparece"><h3>{e(c["nombre"])}</h3>
      <ul>{"".join(f"<li>{e(p)}</li>" for p in c["puntos"])}</ul></div>''' for c in cr["columnas"])
    return f'''<section class="parte parte--suave" id="por-que" aria-labelledby="t-por-que">
  <div class="wrap">
    <span class="etiqueta">El hueco</span>
    <h2 class="titulo aparece" id="t-por-que">{e(cr["titulo"])}</h2>
    <p class="entradilla aparece">{e(cr["intro"])}</p>
    <div class="rol-grid">{cols}</div>
  </div>
</section>'''


def productos_html(co):
    pr = co.get("productos")
    if not pr:
        return ""
    fichas = "".join(f'''<article class="producto aparece">
      {arte_reticula(300 + i, "arte-tarjeta")}
      <span class="anos">{e(p["anos"])}</span>{f'<span class="sello">{e(p["sello"])}</span>' if lleno(p.get("sello")) else ""}
      <span class="producto-tipo">{e(p.get("tipo", ""))}</span>
      <h3>{e(p["nombre"])}</h3>
      <p>{e(p["texto"])}</p>
    </article>''' for i, p in enumerate(pr["items"]))
    return f'''<section class="parte productos-sec" id="productos" aria-labelledby="t-productos">
  <div class="wrap">
    <span class="etiqueta">Producto</span>
    <h2 class="titulo aparece" id="t-productos">{e(pr["titulo"])}</h2>
    <p class="entradilla aparece">{e(pr["intro"])}</p>
    <div class="productos">{fichas}</div>
  </div>
</section>'''


def consultor():
    co = C["consultor"]
    tray = "".join(f'''<article class="tarjeta">
      {arte_reticula(100 + i, "arte-tarjeta")}
      <span class="anos">{e(t["anos"])}</span>
      <h3>{e(t["nombre"])}</h3>
      <p>{e(t["texto"])}</p>
    </article>''' for i, t in enumerate(co["trayectoria"]) if lleno(t.get("nombre")))
    ilumya = ""
    il = co.get("ilumya", {})
    if il.get("mostrar"):
        ilumya = f'''<div class="empresa aparece">
      <div class="empresa-marca"><span class="etiqueta">{e(il.get("subtitulo", ""))}</span><h3>{(f'<img class="empresa-logo" src="/{e(il["logo"])}" alt="{e(il["titulo"])}" width="900" height="296">' if lleno(il.get("logo")) and (BASE / il["logo"]).exists() else e(il["titulo"]))}</h3><p class="empresa-frase">{e(il.get("frase", ""))}</p></div>
      <div class="empresa-texto"><p>{e(il.get("texto", ""))}</p>
        <a class="boton boton--lg" href="{e(il["url"])}" target="_blank" rel="noopener">{e(il.get("boton", "Ver más"))} ↗</a></div>
    </div>'''
    def form_item(it):
        nota = f'<p>{e(it["nota"])}</p>' if lleno(it.get("nota")) else ""
        return f'''<li><span class="form-anos">{e(it["anos"])}</span><h4>{e(it["titulo"])}</h4>
          <span class="form-centro">{e(it["centro"])}</span>{nota}</li>'''
    fm = co.get("formacion")
    if isinstance(fm, list) and fm:
        grupos = "".join(f'''<div class="form-grupo aparece"><h3>{e(g["grupo"])} <small>{len(g["items"])}</small></h3>
          <ul>{"".join(form_item(i) for i in g["items"])}</ul></div>''' for g in fm)
        formacion = f'''<div class="formacion2" id="formacion">
      <span class="etiqueta">Formación</span>
      <h2 class="titulo aparece">{e(co.get("formacion_titulo", "Formación"))}</h2>
      {f'<p class="entradilla aparece">{e(co["formacion_intro"])}</p>' if lleno(co.get("formacion_intro")) else ""}
      <div class="form-grid">{grupos}</div>
    </div>'''
    else:
        formacion = (f'<div class="formacion aparece"><strong>Formación</strong><p>{e(fm)}</p></div>' if lleno(fm) else "")
    foto = co.get("foto_intro", "")
    foto_html = (f'<figure class="intro-foto aparece"><img src="/{e(foto)}" alt="Juanra Doménech trabajando con una tableta" loading="lazy"></figure>'
                 if lleno(foto) and (BASE / foto).exists() else "")
    contenido = f'''{portada_pagina("consultor", "01", arte_reticula(7), co.get("foto_cabecera", ""))}
<section class="parte" aria-labelledby="t-intro-consultor">
  <span class="marca-agua" aria-hidden="true">{e(co.get("rol", "Consultor"))}</span>
  <div class="wrap">
    <div class="intro{" intro--foto" if foto_html else ""}">
      <div>
        <span class="etiqueta">01 · {e(co.get("rol", "Consultor"))}</span>
        <h2 class="titulo aparece" id="t-intro-consultor">{e(co["titulo"])}</h2>
        {f'<p class="tiempo-destacado lema-pro aparece"><span>{e(co["lema"])}</span></p>' if lleno(co.get("lema")) else ""}
        <p class="entradilla aparece">{e(co["entradilla"])}</p>
        <p class="intro-acciones aparece"><a class="boton boton--lg" href="{"#metodo" if co.get("metodo") else "#servicios"}">{"Cómo trabajo" if co.get("metodo") else "Ver servicios"}</a><a class="boton boton--lg boton--linea" href="#contacto">Hablemos</a></p>
      </div>
      {foto_html}
    </div>
    {cifras_html(co["cifras"])}
    {ilumya}
  </div>
</section>
{metodo_html(co)}
{piramide_html(co)}
{comparativa_rol_html(co)}
{productos_html(co)}
{servicios_html(co) if co.get("mostrar_servicios", True) else ""}
{linkedin_html(co)}
<section class="parte trayectoria-sec" aria-labelledby="t-trayectoria">
  <div class="wrap">
    <span class="etiqueta">Trayectoria</span>
    <h2 class="titulo aparece" id="t-trayectoria">De 1997 a hoy</h2>
  </div>
  {carrusel("trayectoria", "Trayectoria profesional", tray)}
  <div class="wrap">{formacion}</div>
</section>'''
    return head(f'{co["titulo"]} · Juanra Doménech', co["entradilla"][:155], "/consultor") + cuerpo("consultor", contenido)


def marcas_html(ci):
    marcas = [m for m in ci.get("marcas", []) if lleno(m.get("nombre"))]
    if not marcas:
        return ""
    celdas = []
    for m in marcas:
        logo = m.get("logo", "")
        if lleno(logo) and (BASE / logo).exists():
            dentro = f'<img src="/{e(logo)}" alt="{e(m["nombre"])}" loading="lazy">'
        else:
            dentro = f'<span class="marca-texto">{e(m["nombre"])}</span>'
        if lleno(m.get("url")):
            celdas.append(f'<a class="marca" href="{e(m["url"])}" target="_blank" rel="noopener" aria-label="{e(m["nombre"])}">{dentro}</a>')
        else:
            celdas.append(f'<div class="marca">{dentro}</div>')
    return f'''<section class="marcas-sec" aria-labelledby="t-marcas">
  <div class="wrap">
    <h2 class="titulo-sec marcas-titulo" id="t-marcas">{e(ci.get("marcas_titulo", "Marcas"))}</h2>
    <div class="marcas aparece">{"".join(celdas)}</div>
  </div>
</section>'''


def num_es(x):
    try:
        return float(str(x).replace(".", "").replace(",", "."))
    except ValueError:
        return 0.0


def medias_temporada(ci):
    cf = {c.get("sufijo", ""): num_es(c["numero"]) for c in ci.get("cifras", [])}
    salidas = next((num_es(c["numero"]) for c in ci.get("cifras", []) if "salidas" in c.get("texto", "")), 0)
    if not salidas or not cf.get("km") or not cf.get("h"):
        return None
    return {"km": cf["km"] / salidas, "desnivel": cf.get("m", 0) / salidas, "velocidad": cf["km"] / cf["h"]}


def comparativa(u, med):
    if not med:
        return ""
    filas = []
    for clave, nombre, ud in (("km", "Distancia", "km"), ("desnivel", "Desnivel", "m"), ("velocidad", "Media", "km/h")):
        v, m = num_es(u.get(clave)), med[clave]
        if not v or not m:
            continue
        tope = max(v, m) * 1.15
        dif = (v - m) / m * 100
        signo = "+" if dif >= 0 else "−"
        filas.append(f'''<div class="cmp-fila"><span class="cmp-n">{nombre}</span>
          <span class="cmp-barra"><i style="width:{v / tope * 100:.1f}%"></i><b style="left:{m / tope * 100:.1f}%"></b></span>
          <span class="cmp-dif{" cmp-dif--mas" if dif >= 0 else ""}">{signo}{abs(dif):.0f}%</span></div>''')
    return f'''<div class="cmp" aria-label="Comparada con la media de la temporada">{"".join(filas)}
        <p class="cmp-ley"><i></i> esta salida <b></b> mi media de 2026</p></div>'''


def ultimas_html(ci):
    ult = [u for u in ci.get("ultimas", []) if lleno(u.get("nombre"))]
    if not ult:
        return ""
    med = medias_temporada(ci)
    tarjetas = "".join(f'''<a class="salida aparece" href="{e(u["url"])}" target="_blank" rel="noopener">
      <span class="salida-fecha">{e(u["fecha"])}</span>
      <h3>{e(u["nombre"])}</h3>
      <dl class="salida-datos">
        <div><dt>Distancia</dt><dd>{e(u["km"])} <small>km</small></dd></div>
        <div><dt>Desnivel</dt><dd>{e(u["desnivel"])} <small>m</small></dd></div>
        <div><dt>Tiempo</dt><dd>{e(u["tiempo"])}</dd></div>
        <div><dt>Media</dt><dd>{e(u["velocidad"])} <small>km/h</small></dd></div>
      </dl>
      {comparativa(u, med)}
      <span class="ver-mas">Ver en Strava <i>↗</i></span>
    </a>''' for i, u in enumerate(ult))
    strava = C["contacto"].get("strava", "")
    boton = (f'<a class="boton boton--linea" href="{e(strava)}" target="_blank" rel="noopener">Sígueme en Strava</a>'
             if lleno(strava) else "")
    return f'''<section class="parte ultimas-sec" aria-labelledby="t-ultimas">
  <div class="wrap">
    <div class="cabeza-sec cabeza-sec--primera"><div><span class="etiqueta">Strava</span><h2 class="titulo-sec" id="t-ultimas">{e(ci.get("ultimas_titulo", "Últimas salidas"))}</h2></div>{boton}</div>
    <div class="salidas">{tarjetas}</div>
    {f'<p class="fuente">{e(ci["datos_strava"])}</p>' if lleno(ci.get("datos_strava")) else ""}
  </div>
</section>'''


def hitos_html(ci):
    hitos = [h for h in ci.get("hitos", []) if lleno(h.get("titulo"))]
    if not hitos:
        return ""
    tarjetas = []
    for i, h in enumerate(hitos):
        foto = h.get("foto", "")
        if lleno(foto) and (BASE / foto).exists():
            visual = f'<img src="/{e(foto)}" alt="{e(h["titulo"])}" loading="lazy">'
        else:
            visual = arte_curvas()
        tarjetas.append(f'''<article class="hito{" hito--siguiente" if i else ""} aparece">
      <div class="hito-visual">{visual}</div>
      <div class="hito-texto">
        <span class="etiqueta">{e(h.get("etiqueta", ""))}</span>
        <h3>{e(h["titulo"])}</h3>
        <p class="hito-lugar">{e(h.get("lugar", ""))}</p>
        <p>{e(h.get("texto", ""))}</p>
      </div>
    </article>''')
    return f'''<section class="parte hitos-sec" aria-labelledby="t-hitos">
  <div class="wrap">
    <span class="etiqueta">Competición</span>
    <h2 class="titulo aparece" id="t-hitos">{e(ci.get("hitos_titulo", "Hitos"))}</h2>
    <div class="hitos">{"".join(tarjetas)}</div>
  </div>
</section>'''


def ciclista():
    ci = C["ciclista"]
    retos_vis = [r for r in ci.get("retos", []) if lleno(r.get("nombre"))]
    retos = ""
    if retos_vis:
        retos = carrusel("retos", "Retos y marchas", "".join(f'''<article class="tarjeta{" tarjeta--ruta" if lleno(r.get("polyline")) else ""}">
      {arte_ruta(r["polyline"], "arte-tarjeta arte-ruta") if lleno(r.get("polyline")) else arte_altimetria(200 + i, "arte-tarjeta", 700)}
      <span class="anos">{e(r.get("ano", ""))}</span>
      {f'<b class="dato">{e(r["dato"])}</b>' if lleno(r.get("dato")) else ""}
      <h3>{e(r["nombre"])}</h3>
      {f'<p>{e(r["texto"])}</p>' if lleno(r.get("texto")) else ""}
      {f'<a class="ver-mas tarjeta-strava" href="{e(r["url"])}" target="_blank" rel="noopener">Ver la ruta en Strava <i>↗</i></a>' if lleno(r.get("url")) else ""}
    </article>''' for i, r in enumerate(retos_vis)))
        retos = f'<div class="wrap cabeza-sec"><h2 class="titulo-sec">{e(ci.get("retos_titulo", "Retos y marchas"))}</h2></div>' + retos
    elif not ci.get("hitos"):
        retos = f'<div class="wrap"><div class="proximamente aparece"><p>{e(ci["proximamente"])}</p></div></div>'
    foto = ci.get("foto_intro", "")
    foto_html = (f'<figure class="intro-foto intro-foto--bici aparece"><img src="/{e(foto)}" alt="Juanra Doménech con su bicicleta de carretera" loading="lazy"></figure>'
                 if lleno(foto) and (BASE / foto).exists() else "")
    parrafos = "".join(f'<p>{e(p)}</p>' for p in ci.get("parrafos", []))
    cita = f'<blockquote class="cita aparece">{e(ci["cita"])}</blockquote>' if lleno(ci.get("cita")) else ""
    strava = C["contacto"].get("strava", "")
    boton = (f'<p class="intro-acciones"><a class="boton boton--lg" href="{e(strava)}" target="_blank" rel="noopener">Sígueme en Strava</a></p>'
             if lleno(strava) else "")
    contenido = f'''{portada_pagina("ciclista", "02", arte_altimetria(11), ci.get("foto_cabecera", ""))}
<section class="parte parte--suave" aria-labelledby="t-intro-ciclista">
  <span class="marca-agua" aria-hidden="true">Ciclista</span>
  <div class="wrap">
    <div class="intro{" intro--foto" if foto_html else ""}">
      <div>
        <span class="etiqueta">02 · Ciclista</span>
        <h2 class="titulo aparece" id="t-intro-ciclista">{e(ci["titulo"])}</h2>
        <p class="entradilla entradilla--fuerte aparece">{e(ci["entradilla"])}</p>
        <div class="texto-largo aparece">{parrafos}</div>
        {boton}
      </div>
      {foto_html}
    </div>
    {cita}
    {cifras_html(ci["cifras"])}
    {f'<p class="fuente">{e(ci["cifras_nota"])}</p>' if lleno(ci.get("cifras_nota")) else ""}
  </div>
  {retos}
</section>
{ultimas_html(ci)}
{hitos_html(ci)}
{marcas_html(ci)}'''
    return head("Ciclista · Juanra Doménech", (ci["titulo"] + ". " + ci["entradilla"])[:155], "/ciclista") + cuerpo("ciclista", contenido)


# ---------------------------------------------------------------- legales
def pagina(titulo, ruta, cuerpo, indexar=True):
    return head(f"{titulo} · Juanra Doménech", f"{titulo} de juanradomenech.com", ruta, indexar) + f'''</head>
<body>
{cabecera()}
<main id="contenido" class="legal">
  <span class="etiqueta">Legal</span>
  <h1>{e(titulo)}</h1>
  {cuerpo}
  <p class="fecha">Última actualización: {FECHA}.</p>
</main>
{pie()}
{scripts()}
</body>
</html>
'''


def app_pagina(clave):
    import urllib.parse
    a = C["apps"][clave]
    co = C["contacto"]
    url_mail = (f'mailto:{co["correo"]}?subject=' + urllib.parse.quote(a["cta_asunto"])
                + "&body=" + urllib.parse.quote(a["cta_cuerpo"]))
    img = lambda x, cls="": (f'<img class="{cls}" src="/{e(x["src"])}" alt="{e(x["alt"])}" width="{x["ancho"]}" '
                             f'height="{x["alto"]}" loading="lazy" decoding="async">')
    marco = lambda x: f'''<figure class="app-marco"><div class="app-marco-barra"><i></i><i></i><i></i></div>{img(x)}</figure>'''
    funciones = "".join(f'''<li class="aparece"><span>{i:02d}</span><h3>{e(f["titulo"])}</h3><p>{e(f["texto"])}</p></li>'''
                        for i, f in enumerate(a["funciones"], 1))
    capturas = "".join(f'''<figure class="app-captura app-captura--{"alta" if x["alto"] > x["ancho"] else "ancha"} aparece">{img(x)}<figcaption>{e(x["pie"])}</figcaption></figure>'''
                       for x in a["capturas"])
    agenda = co.get("agenda_url", "")
    destino_cta = a.get("cta_url") or url_mail
    boton_cta = f'<a class="boton boton--lg" href="{e(destino_cta)}">{e(a["cta"])}</a>' if lleno(a.get("cta")) else ""
    pg = a.get("pregunta")
    pregunta = (f'''<section class="parte app-pregunta" aria-labelledby="t-pregunta">
  <div class="wrap aparece">
    <h2 class="app-pregunta-titulo" id="t-pregunta">{e(pg["titulo"])}</h2>
    <p class="app-pregunta-texto">{e(pg["texto"])}</p>
  </div>
</section>
''' if pg else "")
    contenido = f'''<section class="parte app-hero" aria-labelledby="t-app">
  <div class="wrap">
    <span class="etiqueta">{e(a["etiqueta"])}</span>
    <h1 class="app-nombre" id="t-app">{e(a["nombre"])}</h1>
    <p class="app-lema">{e(a["lema"])}</p>
    <p class="entradilla">{e(a["entradilla"])}</p>
    <p class="app-acciones">{boton_cta}
      {f'<a class="boton boton--lg boton--linea" href="{e(agenda)}" target="_blank" rel="noopener">{e(a["secundario"])}</a>' if lleno(agenda) and lleno(a.get("secundario")) else ""}</p>
    {marco(a["captura_principal"])}
    <p class="app-aviso">{e(a["aviso"])}</p>
  </div>
</section>
{pregunta}<section class="parte parte--suave" aria-labelledby="t-funciones">
  <div class="wrap">
    <span class="etiqueta">Qué hace</span>
    <h2 class="titulo aparece" id="t-funciones">Menos apuntar, más decidir</h2>
    <ul class="app-funciones">{funciones}</ul>
    <div class="app-capturas">{capturas}</div>
  </div>
</section>
<section class="parte app-precio" aria-labelledby="t-precio">
  <div class="wrap app-precio-caja aparece">
    <div><span class="etiqueta">{e(a["precio_titulo"])}</span>
      <h2 class="titulo" id="t-precio">{e(a.get("precio_h2", "Sé de los primeros"))}</h2>
      <p>{e(a["precio_texto"])}</p>
      <p class="app-condiciones"><a href="/condiciones-pfp.html">Condiciones y privacidad de la app</a></p></div>
    {boton_cta}
  </div>
</section>'''
    return head(f"{a['nombre']} · {a['lema']}", a["entradilla"][:155], "/" + a["ruta"].replace(".html", ""), a.get("indexar", False)) + f'''</head>
<body>
{cabecera(clave)}
<main id="contenido" class="app-pagina">
{contenido}
</main>
{pie()}
{scripts()}
</body>
</html>
'''


def aviso_legal():
    L = C["legal"]
    return pagina("Aviso legal", "/aviso-legal.html", f'''
  <p>En cumplimiento del artículo 10 de la Ley 34/2002, de servicios de la sociedad de la información y de comercio electrónico (LSSI), estos son los datos del titular de juanradomenech.com:</p>
  <ul>
    <li><strong>Titular:</strong> {e(L["titular"])}</li>
    <li><strong>NIF:</strong> {e(L["nif"])}</li>
    <li><strong>Domicilio:</strong> {e(L["domicilio"])}</li>
    <li><strong>Correo:</strong> {e(L["correo_legal"])}</li>
  </ul>
  <h2>Objeto</h2>
  <p>Esta web es la página personal de Juanra Doménech: presenta su actividad profesional como {e(C["consultor"]["titulo"])} y su actividad como ciclista.</p>
  <h2>Propiedad intelectual</h2>
  <p>Los textos, fotografías, grafismos y diseño de esta web son de su titular o se usan con permiso. No se pueden reproducir sin autorización, salvo citas breves con enlace a la fuente.</p>
  <h2>Enlaces</h2>
  <p>La web enlaza a perfiles en redes sociales y a otras páginas. El titular no responde del contenido de páginas de terceros.</p>
  <h2>Legislación</h2>
  <p>Esta web se rige por la legislación española.</p>''')


def privacidad():
    L = C["legal"]
    return pagina("Política de privacidad", "/privacidad.html", f'''
  <h2>Responsable</h2>
  <p>{e(L["titular"])}, NIF {e(L["nif"])}, {e(L["domicilio"])}. Correo: {e(L["correo_legal"])}.</p>
  <h2>Qué datos se tratan</h2>
  <p>Esta web no tiene formularios ni pide registro. Se tratan los datos que tú envíes si me escribes por correo o por una red social: tu nombre, tu dirección de correo y lo que cuentes en el mensaje.{" Si aceptas las cookies de analítica, también datos de navegación (páginas visitadas, tipo de dispositivo, ubicación aproximada) a través de Google Analytics." if GA else ""}</p>
  <h2>Para qué y con qué base</h2>
  <p>Para responderte y, si llegamos a trabajar juntos, para gestionar esa relación. La base es tu consentimiento al escribirme y, en su caso, la aplicación de medidas precontractuales o de un contrato.{" La analítica sirve para mejorar la web y su base es tu consentimiento, que puedes retirar en cualquier momento." if GA else ""}</p>
  <h2>Cuánto tiempo</h2>
  <p>Mientras dure la conversación o la relación profesional y, después, el tiempo que obliguen las leyes.</p>
  <h2>Quién más los trata</h2>
  <p>El proveedor de correo (Google Ireland Limited, con Gmail) y el de alojamiento de la web (Netlify, Inc.), que solo guarda los registros técnicos de acceso necesarios para servir la web.{" Si aceptas la analítica, Google Ireland Limited como encargado (ver la política de cookies)." if GA else ""} No se ceden datos a nadie más salvo obligación legal.</p>
  <h2>Tus derechos</h2>
  <p>Puedes pedir acceso, rectificación, supresión, oposición, limitación y portabilidad escribiendo a {e(L["correo_legal"])}. Si crees que no se han respetado, puedes reclamar ante la Agencia Española de Protección de Datos (<a href="https://www.aepd.es" target="_blank" rel="noopener">aepd.es</a>).</p>''')


def condiciones_pfp():
    L = C["legal"]
    c = e(L["correo_legal"])
    return pagina("Personal Finance PRO · Condiciones y privacidad", "/condiciones-pfp.html", f'''
  <p>Estas condiciones regulan el uso de Personal Finance PRO (en adelante, «la app»), disponible en <a href="https://app.juanradomenech.com">app.juanradomenech.com</a>, y la suscripción PRO. Al crear una cuenta o contratar PRO las aceptas.</p>

  <h2>1. Quién presta el servicio</h2>
  <p>{e(L["titular"])}, NIF {e(L["nif"])}, con domicilio en {e(L["domicilio"])}. Correo de contacto y soporte: <a href="mailto:{c}">{c}</a>.</p>

  <h2>2. Qué es la app</h2>
  <p>Una herramienta para llevar tu presupuesto personal: apuntas gastos escribiendo, dictando o fotografiando tickets, y una inteligencia artificial los coloca en su partida. Es una ayuda para organizarte, no asesoramiento financiero, fiscal ni de inversión. La IA puede equivocarse al leer un ticket o al elegir una partida: revisa lo que importa y corrígelo cuando haga falta.</p>

  <h2>3. Planes</h2>
  <ul>
    <li><strong>Free (gratis):</strong> el panel de presupuesto, 100 créditos de IA en total y hasta 10 elementos en Historial (tickets), Artículos y Análisis (artículos) y Tesorería (movimientos). Cada ticket o mensaje que lee la IA gasta un crédito. Al llegar al límite, la sección pasa a ser PRO; tus datos no se borran.</li>
    <li><strong>PRO:</strong> todas las secciones y la IA sin límite de créditos, más el asesor financiero IA. Cuesta <strong>2,99 € al mes</strong> o <strong>29,99 € al año</strong>, IVA incluido.</li>
  </ul>
  <p>Hago un uso razonable de la IA para mantener el servicio: si una cuenta hiciera un uso claramente abusivo o automatizado, podría limitarla avisando antes por correo.</p>

  <h2>4. Prueba gratis, pago y renovación</h2>
  <ul>
    <li>Al contratar PRO tienes <strong>14 días de prueba gratis</strong>. Si no cancelas antes de que terminen, se cobra el primer periodo (mes o año) y la suscripción <strong>se renueva automáticamente</strong> cada periodo al mismo precio hasta que la canceles.</li>
    <li>El pago lo gestiona Stripe. La app nunca ve ni guarda los datos de tu tarjeta.</li>
    <li>Recibirás la factura de cada cobro en tu correo y podrás descargarlas desde «Tu cuenta → Gestionar suscripción y facturas».</li>
    <li>Si cambio el precio, te avisaré por correo con al menos 30 días de antelación; el nuevo precio solo se aplicará a partir de la siguiente renovación y podrás cancelar antes sin coste.</li>
  </ul>

  <h2>5. Precio de lanzamiento Black Friday</h2>
  <p>Quien contrate PRO hasta el 30 de noviembre de 2026 a las 23:59 (hora peninsular) tiene un <strong>20 % de descuento para siempre</strong>: 2,39 € al mes o 23,99 € al año, IVA incluido. El descuento se mantiene en todas las renovaciones y si cambias entre mensual y anual, mientras la suscripción siga activa. Si la cancelas y vuelves a contratar más adelante, se aplicará el precio vigente en ese momento.</p>

  <h2>6. Cancelar y cambiar de plan</h2>
  <ul>
    <li>Puedes cancelar cuando quieras desde «Tu cuenta → Gestionar suscripción y facturas». La cancelación es efectiva al final del periodo ya pagado: hasta entonces sigues teniendo PRO y no se vuelve a cobrar.</li>
    <li>Si pasas de mensual a anual, el cambio es inmediato y se descuenta la parte no usada del mes. Si pasas de anual a mensual, el cambio se aplica al terminar el año pagado.</li>
    <li>Los periodos ya pagados no se devuelven de forma parcial, salvo lo previsto en el apartado siguiente o lo que diga la ley.</li>
  </ul>

  <h2>7. Derecho de desistimiento</h2>
  <p>Como consumidor, tienes 14 días naturales desde que contratas PRO para desistir sin dar explicaciones (artículos 102 y siguientes de la Ley General para la Defensa de los Consumidores y Usuarios). Esos 14 días coinciden con la prueba gratis: si cancelas dentro de la prueba, no se te cobra nada.</p>
  <p>Además, si se te ha hecho el primer cobro y me lo pides en los 14 días siguientes escribiendo a <a href="mailto:{c}">{c}</a>, te devuelvo ese primer importe completo.</p>

  <h2>8. Tus datos</h2>
  <p>El responsable es {e(L["titular"])} (datos en el apartado 1).</p>
  <ul>
    <li><strong>Qué datos:</strong> tu nombre y correo (y la foto de perfil, si entras con tu cuenta de Google); el presupuesto, los gastos, los tickets (texto e imagen que envíes), los artículos y los movimientos que guardes; el uso de créditos; y, si contratas PRO, los datos de la suscripción (no los de la tarjeta).</li>
    <li><strong>Para qué:</strong> para prestarte el servicio, leer tus tickets y mensajes con IA, gestionar el cobro y atenderte. La base es el contrato que aceptas al registrarte y, en lo relativo a facturación, el cumplimiento de obligaciones legales.</li>
    <li><strong>Quién más los trata, por encargo mío:</strong> Google (Firebase, para el acceso, el almacenamiento en la nube y la IA Gemini que lee tickets y mensajes) y Stripe (pagos y facturas). Pueden tratar datos fuera del Espacio Económico Europeo con las garantías que exige el RGPD (cláusulas contractuales tipo y marcos de adecuación). No se venden ni se ceden datos a nadie más salvo obligación legal.</li>
    <li><strong>Cuánto tiempo:</strong> mientras tengas la cuenta. Si me pides borrarla, elimino tus datos en un plazo máximo de 30 días, salvo los de facturación, que se guardan el tiempo que obliga la ley fiscal.</li>
    <li><strong>Tus derechos:</strong> acceso, rectificación, supresión, oposición, limitación y portabilidad, escribiendo a <a href="mailto:{c}">{c}</a>. Puedes reclamar ante la Agencia Española de Protección de Datos (<a href="https://www.aepd.es" target="_blank" rel="noopener">aepd.es</a>).</li>
  </ul>

  <h2>9. Disponibilidad y responsabilidad</h2>
  <p>Pongo los medios razonables para que la app funcione bien y tus datos se guarden de forma segura, pero puede haber interrupciones por mantenimiento o por fallos de los proveedores. Las decisiones económicas que tomes con la información de la app son tuyas. Nada de esto limita los derechos que te reconoce la ley como consumidor.</p>

  <h2>10. Cambios en estas condiciones</h2>
  <p>Si cambio algo importante, te avisaré por correo o dentro de la app con al menos 30 días de antelación. Si no estás de acuerdo, puedes cancelar antes de que entren en vigor.</p>

  <h2>11. Ley aplicable</h2>
  <p>Se aplica la ley española. Si eres consumidor, son competentes los juzgados de tu domicilio.</p>''')


def cookies():
    if not GA:
        return pagina("Política de cookies", "/cookies.html", '''
  <p>Esta web <strong>no usa cookies</strong>: ni propias ni de terceros, ni de analítica ni de publicidad. Tampoco guarda nada en tu navegador. Por eso no verás ningún aviso de cookies.</p>
  <p>Las tipografías se sirven desde este mismo dominio, sin llamar a servicios externos.</p>''')
    return pagina("Política de cookies", "/cookies.html", '''
  <p>Esta web usa cookies de analítica de <strong>Google Analytics</strong> para saber cuántas personas la visitan, cómo llegan y qué páginas leen. <strong>Solo se activan si las aceptas</strong> en el aviso que aparece al entrar. Si las rechazas, la web funciona igual.</p>
  <h2>Qué cookies se usan</h2>
  <ul>
    <li><strong>_ga</strong> (Google Analytics): distingue a los visitantes de forma anónima. Dura 2 años.</li>
    <li><strong>_ga_&lt;ID&gt;</strong> (Google Analytics): guarda el estado de la sesión. Dura 2 años.</li>
  </ul>
  <p>Además, la web guarda en tu navegador (almacenamiento local, no es una cookie) si aceptaste o rechazaste, para no volver a preguntarte: <strong>jd_cookies</strong>. Es necesaria y no se envía a nadie.</p>
  <h2>Quién las gestiona</h2>
  <p>Google Ireland Limited. Los datos pueden transferirse a Estados Unidos al amparo del Marco de Privacidad de Datos UE-EE. UU. Más información en la <a href="https://policies.google.com/technologies/partner-sites?hl=es" target="_blank" rel="noopener">información de Google sobre cómo usa los datos</a>.</p>
  <h2>Cómo cambiar tu decisión</h2>
  <p>Puedes cambiarla cuando quieras con el botón <strong>«Configurar cookies»</strong> del pie de cualquier página, o borrando las cookies desde los ajustes de tu navegador.</p>''')


def error404():
    return head("Página no encontrada · Juanra Doménech", "Esta página no existe.", "/404.html", False) + f'''</head>
<body>
{cabecera()}
<main id="contenido" class="error">
  <h1>404</h1>
  <p>Esta carretera no lleva a ninguna parte.</p>
  <p><a class="boton boton--lg" href="/">Volver al inicio</a></p>
</main>
{scripts()}
</body>
</html>
'''


# ---------------------------------------------------------------- otros archivos
FAVICON = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs><radialGradient id="b" cx="34%" cy="28%" r="78%"><stop offset="0" stop-color="#5a5a5a"/><stop offset=".45" stop-color="#161616"/><stop offset="1" stop-color="#000"/></radialGradient></defs><circle cx="32" cy="32" r="31" fill="url(#b)"/><circle cx="29.5" cy="27.5" r="14" fill="#f4f4f4"/><text x="29.5" y="35.2" text-anchor="middle" font-family="Arial Narrow, Helvetica, Arial, sans-serif" font-weight="700" font-size="22" fill="#000">8</text><ellipse cx="18" cy="15" rx="6.5" ry="3.4" fill="#fff" opacity=".35" transform="rotate(-30 18 15)"/></svg>'''

REDIRECTS = """# www -> dominio principal
https://www.juanradomenech.com/*  https://juanradomenech.com/:splat  301!
http://www.juanradomenech.com/*   https://juanradomenech.com/:splat  301!
"""

HEADERS = """/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self'; font-src 'self'; script-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'

/fonts/*
  Cache-Control: public, max-age=31536000, immutable
"""


def cabeceras():
    if not GA:
        return HEADERS
    g = "https://www.googletagmanager.com"
    a = ("https://*.google-analytics.com https://*.analytics.google.com https://*.googletagmanager.com "
         "https://*.g.doubleclick.net https://www.google.com")
    return HEADERS.replace("img-src 'self' data:", f"img-src 'self' data: {a}").replace(
        "script-src 'self'", f"script-src 'self' {g}").replace(
        "form-action 'self'", f"connect-src 'self' {a}; form-action 'self'")


def comprobar():
    """Avisos: marcadores pendientes, textos por revisar y rastros que no deben salir."""
    avisos = []
    texto = json.dumps(C, ensure_ascii=False)
    for m in sorted(set(re.findall(r"\[[A-ZÁÉÍÓÚÑ0-9 _]+\]", texto))):
        avisos.append(f"Marcador sin rellenar: {m}")

    def revisar(nodo, ruta):
        if isinstance(nodo, dict):
            if nodo.get("revisar"):
                avisos.append(f"Texto redactado por Claude, por revisar: {ruta}")
            for k, v in nodo.items():
                revisar(v, f"{ruta}.{k}" if ruta else k)
    revisar(C, "")
    if not lleno(C["contacto"].get("correo")):
        avisos.append("Sin correo de contacto: solo se muestra LinkedIn en «Hablemos».")
    if not [x for x in C["ciclista"]["cifras"] if lleno(x.get("numero"))]:
        avisos.append("Ciclista: sin cifras (no se muestran).")
    for m in C["ciclista"].get("marcas", []):
        if lleno(m.get("logo")) and not (BASE / m["logo"]).exists():
            avisos.append(f"Logo pendiente: {m['logo']} (se muestra el nombre «{m['nombre']}» en texto)")
    if not GA:
        avisos.append("Analítica: sin ID de Google Analytics (analitica.ga4_id). No hay cookies ni aviso.")
    if not C["ciclista"].get("retos"):
        avisos.append("Ciclista: sin retos (se muestra «Próximamente»).")

    prohibidas = ["cristiano", "ronaldo", "cr7", "7egend", "typekit"]
    if not C["consultor"].get("ilumya", {}).get("mostrar"):
        prohibidas.append("ilumya")
    for f in SALIDA.rglob("*"):
        if f.is_file() and f.suffix in {".html", ".css", ".js", ".txt", ".xml", ".svg", ""} and not f.name.startswith("OFL"):
            t = f.read_text(encoding="utf-8").lower()
            for p in prohibidas:
                if p in t:
                    avisos.append(f"ERROR: «{p}» aparece en {f.relative_to(SALIDA)}")
    return avisos


def version_local():
    """Carpeta local/: cada página con el CSS, el JS y las fuentes dentro, para abrirla con doble clic."""
    import base64
    LOCAL = BASE / "local"
    if LOCAL.exists():
        shutil.rmtree(LOCAL)
    LOCAL.mkdir()
    css = (SALIDA / "css/estilos.css").read_text(encoding="utf-8")
    css = re.sub(r'url\("\.\./(fonts/[^"]+)"\)', lambda m: 'url("data:font/woff2;base64,'
                 + base64.b64encode((SALIDA / m.group(1)).read_bytes()).decode() + '")', css)
    js = (SALIDA / "js/web.js").read_text(encoding="utf-8")
    fav = "data:image/svg+xml;base64," + base64.b64encode((SALIDA / "favicon.svg").read_bytes()).decode()
    for f in SALIDA.glob("*.html"):
        if f.name == "404.html":
            continue
        h = f.read_text(encoding="utf-8")
        h = re.sub(r'<link rel="preload"[^>]*>\n', "", h)
        h = h.replace('<link rel="stylesheet" href="css/estilos.css">', "<style>\n" + css + "\n</style>")
        h = h.replace('<script src="js/web.js" defer></script>', "<script>\n" + js + "\n</script>")
        if GA:
            cj = (SALIDA / "js/consentimiento.js").read_text(encoding="utf-8")
            h = h.replace('<script src="js/consentimiento.js" defer></script>', "<script>\n" + cj + "\n</script>")
        h = h.replace('href="favicon.svg"', f'href="{fav}"')
        for m in re.findall(r'src="(media/[^"]+)"', h):
            tipo = {"svg": "image/svg+xml", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(m.rsplit(".", 1)[-1].lower(), "application/octet-stream")
            h = h.replace(f'src="{m}"', f'src="data:{tipo};base64,' + base64.b64encode((SALIDA / m).read_bytes()).decode() + '"')
        (LOCAL / f.name).write_text(h, encoding="utf-8")


def main():
    if SALIDA.exists():
        shutil.rmtree(SALIDA)
    shutil.copytree(BASE / "recursos", SALIDA)
    if (BASE / "media").exists():
        shutil.copytree(BASE / "media", SALIDA / "media", dirs_exist_ok=True, ignore=shutil.ignore_patterns("LEEME.txt"))
    paginas = {
        "index.html": index(),
        "consultor.html": consultor(),
        "ciclista.html": ciclista(),
        "aviso-legal.html": aviso_legal(),
        "privacidad.html": privacidad(),
        "cookies.html": cookies(),
        "condiciones-pfp.html": condiciones_pfp(),
        "404.html": error404(),
    }
    for clave, a in C.get("apps", {}).items():
        if a.get("publicar"):
            paginas[a["ruta"]] = app_pagina(clave)
    for nombre, contenido in paginas.items():
        if nombre != "404.html":  # rutas relativas: funcionan en Netlify y en cualquier carpeta
            contenido = (contenido.replace('href="/"', 'href="index.html"')
                         .replace('href="/', 'href="').replace('src="/', 'src="'))
        (SALIDA / nombre).write_text(contenido, encoding="utf-8")
    dom = C["sitio"]["dominio"].rstrip("/")
    (SALIDA / "favicon.svg").write_text(FAVICON, encoding="utf-8")
    (SALIDA / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {dom}/sitemap.xml\n", encoding="utf-8")
    urls = ["/", "/consultor", "/ciclista", "/aviso-legal.html", "/privacidad.html", "/cookies.html"]
    (SALIDA / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{dom}{u}</loc><lastmod>{HOY.isoformat()}</lastmod></url>\n" for u in urls)
        + "</urlset>\n", encoding="utf-8")
    (SALIDA / "_redirects").write_text(REDIRECTS, encoding="utf-8")
    (SALIDA / "_headers").write_text(cabeceras(), encoding="utf-8")

    version_local()
    # Versión en las rutas de CSS y JS para que el navegador no use una copia antigua tras publicar
    import hashlib
    ver = {r: hashlib.md5((SALIDA / r).read_bytes()).hexdigest()[:8] for r in ("css/estilos.css", "js/web.js", "js/consentimiento.js") if (SALIDA / r).exists()}
    for f in SALIDA.glob("*.html"):
        h = f.read_text(encoding="utf-8")
        for r, v in ver.items():
            h = h.replace(f'"{r}"', f'"{r}?v={v}"').replace(f'"/{r}"', f'"/{r}?v={v}"')
        f.write_text(h, encoding="utf-8")
    avisos = comprobar()
    print(f"Web generada en {SALIDA}")
    for a in avisos:
        print(" ·", a)
    if any(a.startswith("ERROR") for a in avisos):
        sys.exit(1)


if __name__ == "__main__":
    main()

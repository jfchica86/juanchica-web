"""Construye juanchica.com en docs/ (lo que publica GitHub Pages), en español y en inglés.

Uso:  python3 construir.py
Entradas: contenido/entradas/*.md (español) y contenido/en/entradas/*.md (inglés, mismo nombre
de archivo), cada una con cabecera:

    ---
    titulo: El título
    fecha: 2026-10-25
    bajada: Una o dos líneas que resumen la entrada.
    publicada: si          (si no dice "si", queda como borrador y no sale)
    ---
    Texto en Markdown…

El slug (la dirección) sale del nombre del archivo: 2026-10-25-mi-entrada.md → /blog/mi-entrada/
(y /en/blog/mi-entrada/ en inglés). Páginas: contenido/paginas/<slug>.md → /<slug>/ y
contenido/en/paginas/<slug>.md → /en/<slug>/; PAGINAS_EN dice cuál es la pareja de cada una.
Audio con la voz de Juan: contenido/audio/<slug>.m4a (o .mp3) → reproductor arriba de la entrada en español.
Se comprime antes con: afconvert -f m4af -d aac -b 64000 entrada.mp3 contenido/audio/<slug>.m4a
Requiere: pip install markdown
"""
import hashlib
import html
import json
import re
import shutil
from datetime import date
from pathlib import Path

import markdown

RAIZ = Path(__file__).parent
SALIDA = RAIZ / "docs"
PLANTILLA = RAIZ / "plantilla"
SITIO = json.loads((RAIZ / "sitio.json").read_text(encoding="utf-8"))
ISOTIPO = (PLANTILLA / "isotipo.svg").read_text(encoding="utf-8")
# Cambia con cada versión de la hoja de estilos, para que el navegador no muestre la vieja
VERSION_CSS = hashlib.md5((PLANTILLA / "estilos.css").read_bytes()).hexdigest()[:8]
FUENTES = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
           '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
           '<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@300;400;500;600&display=swap" rel="stylesheet">')

REDES = [("LinkedIn", "https://www.linkedin.com/in/jfchica/", "in/jfchica"),
         ("Substack", "https://juanfranciscochica.substack.com", "juanfranciscochica"),
         ("X", "https://x.com/JFChica", "@JFChica"),
         ("Instagram", "https://www.instagram.com/jfchica/", "@jfchica")]

# Página en español → su pareja en inglés (las que no están aquí conservan el mismo slug)
PAGINAS_EN = {"sobre-mi": "about"}

IDIOMAS = {
    "es": {
        "base": "/", "contenido": RAIZ / "contenido",
        "meses": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                  "septiembre", "octubre", "noviembre", "diciembre"],
        "sobre": "Sobre mí", "sobre_slug": "sobre-mi", "entrar": "Entrar", "inicio": "Inicio",
        "proyectos": "Proyectos", "encuentrame": "Encuéntrame", "leer": "Leer más ›",
        "conocer": "Conocer ›", "vacio": "Las primeras entradas están en camino.",
        "todas": "Todas las entradas de juanchica.com", "escuchar": "Escuchar con mi voz",
        "otro": "EN", "otro_nombre": "English",
    },
    "en": {
        "base": "/en/", "contenido": RAIZ / "contenido" / "en",
        "meses": ["January", "February", "March", "April", "May", "June", "July", "August",
                  "September", "October", "November", "December"],
        "sobre": "About", "sobre_slug": "about", "entrar": "Sign in", "inicio": "Home",
        "proyectos": "Projects", "encuentrame": "Find me", "leer": "Read more ›",
        "conocer": "Learn more ›", "vacio": "The first posts are on their way.",
        "todas": "All posts on juanchica.com", "escuchar": "Listen in my voice",
        "otro": "ES", "otro_nombre": "Español",
    },
}

e = html.escape


def fecha_larga(d: date, lang: str) -> str:
    mes = IDIOMAS[lang]["meses"][d.month - 1]
    return f"{mes} {d.day}, {d.year}" if lang == "en" else f"{d.day} de {mes} de {d.year}"


def leer_cabecera(f: Path):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", f.read_text(encoding="utf-8"), re.S)
    if not m:
        raise SystemExit(f"{f}: falta la cabecera entre --- y ---")
    meta = {}
    for linea in m.group(1).splitlines():
        if ":" in linea:
            k, v = linea.split(":", 1)
            meta[k.strip().lower()] = html.unescape(v.strip())
    return meta, m.group(2)


def leer_entradas(lang: str):
    entradas = []
    for f in sorted((IDIOMAS[lang]["contenido"] / "entradas").glob("*.md")):
        meta, cuerpo = leer_cabecera(f)
        if meta.get("publicada", "").lower() not in ("si", "sí", "true"):
            continue
        for campo in ("titulo", "fecha"):
            if not meta.get(campo):
                raise SystemExit(f"{f.name}: falta '{campo}' en la cabecera")
        entradas.append({
            "slug": re.sub(r"^\d{4}-\d{2}-\d{2}-", "", f.stem),
            "titulo": meta["titulo"],
            "fecha": date.fromisoformat(meta["fecha"]),
            "bajada": meta.get("bajada", ""),
            "html": markdown.markdown(cuerpo, extensions=["extra", "smarty", "sane_lists"]),
        })
    return sorted(entradas, key=lambda x: x["fecha"], reverse=True)


def pagina(lang: str, titulo: str, descripcion: str, cuerpo: str, ruta: str, ruta_otro: str | None) -> str:
    """ruta: dirección de esta página sin la base del idioma ('' = portada, 'blog/' …).
    ruta_otro: la misma página en el otro idioma, o None si no existe (el botón lleva a su portada)."""
    t, base = IDIOMAS[lang], IDIOMAS[lang]["base"]
    otro = "en" if lang == "es" else "es"
    destino = IDIOMAS[otro]["base"] + (ruta_otro if ruta_otro is not None else "")
    url = f"https://{SITIO['dominio']}{base}{ruta}"
    alterna = (f'<link rel="alternate" hreflang="{otro}" href="https://{SITIO["dominio"]}{destino}">'
               if ruta_otro is not None else "")
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descripcion)}">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(descripcion)}">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="{lang}" href="{url}">
{alterna}
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
{FUENTES}
<link rel="stylesheet" href="/assets/estilos.css?v={VERSION_CSS}">
</head>
<body>
<header class="cabecera"><div class="marco">
  <a class="marca" href="{base}" aria-label="{t['inicio']}">{ISOTIPO}<span>juanchica</span></a>
  <nav class="nav">
    <a href="{base}{t['sobre_slug']}/">{t['sobre']}</a>
    <a href="{base}blog/">Blog</a>
    <a class="idioma" href="{destino}" hreflang="{otro}" lang="{otro}" title="{t['otro_nombre']}">{t['otro']}</a>
    <a class="boton" href="{e(SITIO['apps_url'])}">{t['entrar']}</a>
  </nav>
</div></header>
{cuerpo}
<footer class="pie"><div class="marco">
  <span>juanchica.com</span>
  <nav class="redes">{"".join(f'<a href="{u}">{n}</a>' for n, u, _ in REDES)}</nav>
</div></footer>
</body>
</html>
"""


def extracto(x, palabras=45) -> str:
    texto = html.unescape(re.sub(r"<[^>]+>", " ", x["html"])).split()
    return " ".join(texto[:palabras]) + ("…" if len(texto) > palabras else "")


def resumenes(entradas, lang: str) -> str:
    t, base = IDIOMAS[lang], IDIOMAS[lang]["base"]
    if not entradas:
        return f'<p class="vacio">{t["vacio"]}</p>'
    return "".join(
        f'<article class="resumen"><h2><a href="{base}blog/{x["slug"]}/">{e(x["titulo"])}</a></h2>'
        + (f'<p class="bajada">{e(x["bajada"])}</p>' if x["bajada"] else "")
        + f'<p class="extracto">{e(extracto(x))} <a class="mas" href="{base}blog/{x["slug"]}/">{t["leer"]}</a></p>'
        + f'<p class="fecha">{fecha_larga(x["fecha"], lang)}</p></article>'
        for x in entradas
    )


def archivo(entradas, lang: str) -> str:
    t, base = IDIOMAS[lang], IDIOMAS[lang]["base"]
    if not entradas:
        return f'<p class="vacio">{t["vacio"]}</p>'
    bloques, anio = [], None
    for x in entradas:
        if x["fecha"].year != anio:
            if anio is not None:
                bloques.append("</ul>")
            anio = x["fecha"].year
            bloques.append(f'<p class="rotulo">{anio}</p><ul class="archivo">')
        bloques.append(f'<li><a href="{base}blog/{x["slug"]}/">{e(x["titulo"])}</a></li>')
    return "".join(bloques) + "</ul>"


def escribir(ruta_relativa: str, contenido: str):
    destino = SALIDA / ruta_relativa / "index.html"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(contenido, encoding="utf-8")


def construir_idioma(lang: str, slugs_otro: set[str]) -> tuple[int, int]:
    t, base = IDIOMAS[lang], IDIOMAS[lang]["base"]
    textos = SITIO if lang == "es" else SITIO["en"]
    carpeta = base.strip("/")
    pref = f"{carpeta}/" if carpeta else ""
    entradas = leer_entradas(lang)

    # Portada: presentación corta, proyectos, redes y la corriente de entradas
    proyectos = "".join(
        f'<article class="resumen"><h2><a href="{base}{e(p["url"])}">{e(p["nombre"])}</a></h2>'
        f'<p class="extracto">{e(p["texto"])} <a class="mas" href="{base}{e(p["url"])}">{t["conocer"]}</a></p></article>'
        for p in textos["proyectos"]
    )
    redes = "".join(
        f'<article class="resumen"><h2><a href="{u}">{n}</a></h2>'
        f'<p class="extracto"><a class="cuenta" href="{u}">{e(c)}</a></p></article>'
        for n, u, c in REDES
    )
    portada = f"""<main class="marco">
<section class="inicio">
  <p class="intro"><span class="quien">{e(textos['bio'])}</span>{e(textos.get('bio_detalle', ''))} {e(textos.get('bio_temas', ''))}</p>
  <p class="rotulo">{t['proyectos']}</p>
  <div class="tarjetas dos">{proyectos}</div>
  <p class="rotulo">{t['encuentrame']}</p>
  <div class="tarjetas cuatro">{redes}</div>
</section>
<section class="corriente"><p class="rotulo">Blog</p>{resumenes(entradas, lang)}</section>
</main>"""
    descripcion = " ".join(textos.get(k, "") for k in ("bio", "bio_detalle", "bio_temas"))
    escribir(carpeta, pagina(lang, "juanchica", descripcion, portada, "", ""))

    # Blog: todos los títulos, por año
    indice = f"""<main class="marco entrada">
  <h1>Blog</h1>
  {archivo(entradas, lang)}
</main>"""
    escribir(f"{pref}blog", pagina(lang, "Blog · juanchica", t["todas"], indice, "blog/", "blog/"))

    for x in entradas:
        audio = next((a for ext in ("m4a", "mp3") if (a := RAIZ / "contenido" / "audio" / f"{x['slug']}.{ext}").exists()), None)
        reproductor = (f'<div class="audio"><p class="audio-rotulo">{t["escuchar"]}</p>'
                       f'<audio controls preload="metadata" src="/assets/audio/{audio.name}"></audio></div>'
                       if lang == "es" and audio else "")
        cuerpo = f"""<main class="marco entrada"><article>
  <p class="meta">{fecha_larga(x['fecha'], lang)}</p>
  <h1>{e(x['titulo'])}</h1>
  {f'<p class="bajada">{e(x["bajada"])}</p>' if x['bajada'] else ''}
  {reproductor}
  <div class="cuerpo">{x['html']}</div>
  <a class="volver" href="{base}blog/">← Blog</a>
</article></main>"""
        ruta = f"blog/{x['slug']}/"
        escribir(f"{pref}blog/{x['slug']}",
                 pagina(lang, f"{x['titulo']} · juanchica", x["bajada"] or x["titulo"], cuerpo, ruta,
                        ruta if x["slug"] in slugs_otro else None))

    # Páginas sueltas
    paginas = 0
    pareja = PAGINAS_EN if lang == "es" else {v: k for k, v in PAGINAS_EN.items()}
    carpeta_otro = (RAIZ / "contenido" / ("en" if lang == "es" else "") / "paginas")
    for f in sorted((t["contenido"] / "paginas").glob("*.md")):
        meta, texto = leer_cabecera(f)
        slug_otro = pareja.get(f.stem, f.stem)
        cuerpo = f"""<main class="marco entrada"><article>
  <h1>{e(meta.get('titulo', f.stem))}</h1>
  {f'<p class="bajada">{e(meta["bajada"])}</p>' if meta.get('bajada') else ''}
  <div class="cuerpo">{markdown.markdown(texto, extensions=["extra", "smarty"])}</div>
  <a class="volver" href="{base}">← {t['inicio']}</a>
</article></main>"""
        escribir(f"{pref}{f.stem}",
                 pagina(lang, f"{meta.get('titulo', f.stem)} · juanchica", meta.get("bajada", ""), cuerpo,
                        f"{f.stem}/", f"{slug_otro}/" if (carpeta_otro / f"{slug_otro}.md").exists() else None))
        paginas += 1
    return len(entradas), paginas


def construir():
    if SALIDA.exists():
        shutil.rmtree(SALIDA)
    (SALIDA / "assets").mkdir(parents=True)
    shutil.copy(PLANTILLA / "estilos.css", SALIDA / "assets" / "estilos.css")
    # Fotos: contenido/imagenes/x.jpg → /assets/img/x.jpg · audios: contenido/audio → /assets/audio
    if (RAIZ / "contenido" / "imagenes").exists():
        shutil.copytree(RAIZ / "contenido" / "imagenes", SALIDA / "assets" / "img")
    if (RAIZ / "contenido" / "audio").exists():
        shutil.copytree(RAIZ / "contenido" / "audio", SALIDA / "assets" / "audio")
    (SALIDA / "assets" / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#1B1A17"/>'
        + ISOTIPO.replace("<svg ", "<svg x='15' y='14' width='34' height='36' style='color:#F2EEE6' ", 1) + "</svg>",
        encoding="utf-8",
    )
    # El dominio se activa solo cuando el DNS de juanchica.com ya apunte a GitHub Pages.
    if SITIO.get("dominio_activo"):
        (SALIDA / "CNAME").write_text(SITIO["dominio"] + "\n", encoding="utf-8")
    (SALIDA / ".nojekyll").write_text("", encoding="utf-8")

    slugs = {lang: {x["slug"] for x in leer_entradas(lang)} for lang in IDIOMAS}
    for lang in IDIOMAS:
        n, p = construir_idioma(lang, slugs["en" if lang == "es" else "es"])
        print(f"Listo ({lang}): portada + blog con {n} entrada(s) y {p} página(s)")


if __name__ == "__main__":
    construir()

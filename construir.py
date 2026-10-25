"""Construye juanchica.com en docs/ (lo que publica GitHub Pages).

Uso:  python3 construir.py
Entradas: contenido/entradas/*.md, cada una con cabecera:

    ---
    titulo: El título
    fecha: 2026-10-25
    bajada: Una o dos líneas que resumen la entrada.
    publicada: si          (si no dice "si", queda como borrador y no sale)
    ---
    Texto en Markdown…

El slug (la dirección) sale del nombre del archivo: 2026-10-25-mi-entrada.md → /blog/mi-entrada/
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
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
FUENTES = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
           '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
           '<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@300;400;500;600&display=swap" rel="stylesheet">')

REDES = [("LinkedIn", "https://www.linkedin.com/in/jfchica/"),
         ("Substack", "https://juanfranciscochica.substack.com"),
         ("X", "https://x.com/JFChica"),
         ("Instagram", "https://www.instagram.com/jfchica/")]

e = html.escape


def fecha_larga(d: date) -> str:
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def leer_entradas():
    entradas = []
    for f in sorted((RAIZ / "contenido" / "entradas").glob("*.md")):
        texto = f.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", texto, re.S)
        if not m:
            raise SystemExit(f"{f.name}: falta la cabecera entre --- y ---")
        meta = {}
        for linea in m.group(1).splitlines():
            if ":" in linea:
                k, v = linea.split(":", 1)
                meta[k.strip().lower()] = html.unescape(v.strip())
        if meta.get("publicada", "").lower() not in ("si", "sí", "true"):
            continue
        for campo in ("titulo", "fecha"):
            if not meta.get(campo):
                raise SystemExit(f"{f.name}: falta '{campo}' en la cabecera")
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", f.stem)
        entradas.append({
            "slug": slug,
            "titulo": meta["titulo"],
            "fecha": date.fromisoformat(meta["fecha"]),
            "bajada": meta.get("bajada", ""),
            "html": markdown.markdown(m.group(2), extensions=["extra", "smarty", "sane_lists"]),
        })
    return sorted(entradas, key=lambda x: x["fecha"], reverse=True)


def pagina(titulo: str, descripcion: str, cuerpo: str, ruta_css: str, raiz: str) -> str:
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descripcion)}">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(descripcion)}">
<link rel="icon" href="{raiz}assets/favicon.svg" type="image/svg+xml">
{FUENTES}
<link rel="stylesheet" href="{ruta_css}?v={VERSION_CSS}">
</head>
<body>
<header class="cabecera"><div class="marco">
  <a class="marca" href="{raiz}" aria-label="Inicio">{ISOTIPO}<span>juanchica</span></a>
  <nav class="nav">
    <a href="{raiz}sobre-mi/">Sobre mí</a>
    <a href="{raiz}blog/">Blog</a>
    <a class="boton" href="{e(SITIO['apps_url'])}">Entrar</a>
  </nav>
</div></header>
{cuerpo}
<footer class="pie"><div class="marco">
  <span>juanchica.com</span>
  <nav class="redes">{"".join(f'<a href="{u}">{n}</a>' for n, u in REDES)}</nav>
</div></footer>
</body>
</html>
"""


def extracto(x, palabras=45) -> str:
    texto = html.unescape(re.sub(r"<[^>]+>", " ", x["html"])).split()
    return " ".join(texto[:palabras]) + ("…" if len(texto) > palabras else "")


def resumenes(entradas, raiz: str) -> str:
    if not entradas:
        return '<p class="vacio">Las primeras entradas están en camino.</p>'
    return "".join(
        f'<article class="resumen"><h2><a href="{raiz}blog/{x["slug"]}/">{e(x["titulo"])}</a></h2>'
        + (f'<p class="bajada">{e(x["bajada"])}</p>' if x["bajada"] else "")
        + f'<p class="extracto">{e(extracto(x))} <a class="mas" href="{raiz}blog/{x["slug"]}/">Leer más ›</a></p>'
        + f'<p class="fecha">{fecha_larga(x["fecha"])}</p></article>'
        for x in entradas
    )


def archivo(entradas, raiz: str) -> str:
    if not entradas:
        return '<p class="vacio">Las primeras entradas están en camino.</p>'
    bloques, anio = [], None
    for x in entradas:
        if x["fecha"].year != anio:
            if anio is not None:
                bloques.append("</ul>")
            anio = x["fecha"].year
            bloques.append(f'<p class="rotulo">{anio}</p><ul class="archivo">')
        bloques.append(f'<li><a href="{raiz}blog/{x["slug"]}/">{e(x["titulo"])}</a></li>')
    return "".join(bloques) + "</ul>"


def construir():
    entradas = leer_entradas()
    if SALIDA.exists():
        shutil.rmtree(SALIDA)
    (SALIDA / "assets").mkdir(parents=True)
    shutil.copy(PLANTILLA / "estilos.css", SALIDA / "assets" / "estilos.css")
    # Fotos: contenido/imagenes/x.jpg → /assets/img/x.jpg
    if (RAIZ / "contenido" / "imagenes").exists():
        shutil.copytree(RAIZ / "contenido" / "imagenes", SALIDA / "assets" / "img")
    (SALIDA / "assets" / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#1B1A17"/>'
        + ISOTIPO.replace("<svg ", "<svg x='15' y='14' width='34' height='36' style='color:#F2EEE6' ", 1) + "</svg>",
        encoding="utf-8",
    )
    # El dominio se activa solo cuando el DNS de juanchica.com ya apunte a GitHub Pages.
    if SITIO.get("dominio_activo"):
        (SALIDA / "CNAME").write_text(SITIO["dominio"] + "\n", encoding="utf-8")
    (SALIDA / ".nojekyll").write_text("", encoding="utf-8")

    # Portada: presentación corta, enlaces y la corriente de entradas
    proyectos = "".join(f'<a href="{e(p["url"])}">{e(p["nombre"])}</a>' for p in SITIO["proyectos"])
    redes = "".join(f'<a href="{u}">{n}</a>' for n, u in REDES)
    portada = f"""<main class="marco">
<section class="inicio">
  <p class="intro">{e(SITIO['bio'])}</p>
  <p class="rotulo">Proyectos</p>
  <div class="enlaces">{proyectos}<a href="sobre-mi/">Sobre mí</a></div>
  <p class="rotulo">Encuéntrame</p>
  <div class="enlaces">{redes}</div>
</section>
<section class="corriente"><p class="rotulo">Blog</p>{resumenes(entradas, '')}</section>
</main>"""
    (SALIDA / "index.html").write_text(
        pagina("juanchica", SITIO["bio"], portada, "assets/estilos.css", ""), encoding="utf-8")

    # Archivo: todos los títulos, por año
    (SALIDA / "blog").mkdir()
    indice = f"""<main class="marco entrada">
  <h1>Blog</h1>
  {archivo(entradas, '../')}
</main>"""
    (SALIDA / "blog" / "index.html").write_text(
        pagina("Blog · juanchica", "Todas las entradas de juanchica.com", indice, "../assets/estilos.css", "../"), encoding="utf-8")

    for x in entradas:
        d = SALIDA / "blog" / x["slug"]
        d.mkdir()
        cuerpo = f"""<main class="marco entrada"><article>
  <p class="meta">{fecha_larga(x['fecha'])}</p>
  <h1>{e(x['titulo'])}</h1>
  {f'<p class="bajada">{e(x["bajada"])}</p>' if x['bajada'] else ''}
  <div class="cuerpo">{x['html']}</div>
  <a class="volver" href="../">← Blog</a>
</article></main>"""
        (d / "index.html").write_text(
            pagina(f"{x['titulo']} · juanchica", x["bajada"] or x["titulo"], cuerpo, "../../assets/estilos.css", "../../"),
            encoding="utf-8")

    # Páginas sueltas: contenido/paginas/<slug>.md → /<slug>/
    paginas = 0
    for f in sorted((RAIZ / "contenido" / "paginas").glob("*.md")):
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", f.read_text(encoding="utf-8"), re.S)
        if not m:
            raise SystemExit(f"{f.name}: falta la cabecera entre --- y ---")
        meta = dict((k.strip().lower(), v.strip()) for k, v in (l.split(":", 1) for l in m.group(1).splitlines() if ":" in l))
        d = SALIDA / f.stem
        d.mkdir()
        cuerpo = f"""<main class="marco entrada"><article>
  <h1>{e(meta.get('titulo', f.stem))}</h1>
  {f'<p class="bajada">{e(meta["bajada"])}</p>' if meta.get('bajada') else ''}
  <div class="cuerpo">{markdown.markdown(m.group(2), extensions=["extra", "smarty"])}</div>
  <a class="volver" href="../">← Inicio</a>
</article></main>"""
        (d / "index.html").write_text(
            pagina(f"{meta.get('titulo', f.stem)} · juanchica", meta.get("bajada", ""), cuerpo, "../assets/estilos.css", "../"),
            encoding="utf-8")
        paginas += 1

    print(f"Listo: portada + blog con {len(entradas)} entrada(s) publicadas y {paginas} página(s) en docs/")


if __name__ == "__main__":
    construir()

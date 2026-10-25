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
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
FUENTES = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
           '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
           '<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@300;400;500;600&display=swap" rel="stylesheet">')

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
                meta[k.strip().lower()] = v.strip()
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
<link rel="stylesheet" href="{ruta_css}">
</head>
<body>
<header class="cabecera"><div class="contenedor">
  <a class="marca" href="{raiz}" aria-label="Inicio">{ISOTIPO}<span>juanchica</span></a>
  <nav class="nav">
    <a class="texto" href="{raiz}blog/">Blog</a>
    <a class="boton" href="{e(SITIO['apps_url'])}">Entrar</a>
  </nav>
</div></header>
{cuerpo}
<footer class="pie"><div class="contenedor">
  <a class="marca" href="{raiz}">{ISOTIPO}<span>juanchica<span class="dom">.com</span></span></a>
  <p>Colombia</p>
  <a class="boton" href="{e(SITIO['apps_url'])}">Entrar a las apps</a>
</div></footer>
</body>
</html>
"""


def lista(entradas, limite=None):
    if not entradas:
        return '<p class="vacio">Las primeras entradas están en camino.</p>'
    items = []
    for x in entradas[:limite]:
        items.append(
            f'<li><a href="{{raiz}}blog/{x["slug"]}/"><span class="fecha">{fecha_larga(x["fecha"])}</span>'
            f'<h3>{e(x["titulo"])}</h3>' + (f'<p>{e(x["bajada"])}</p>' if x["bajada"] else "") + "</a></li>"
        )
    return '<ul class="lista-entradas">' + "".join(items) + "</ul>"


def construir():
    entradas = leer_entradas()
    if SALIDA.exists():
        shutil.rmtree(SALIDA)
    (SALIDA / "assets").mkdir(parents=True)
    shutil.copy(PLANTILLA / "estilos.css", SALIDA / "assets" / "estilos.css")
    (SALIDA / "assets" / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#1B1A17"/>'
        + ISOTIPO.replace("<svg ", "<svg x='15' y='14' width='34' height='36' style='color:#F2EEE6' ", 1) + "</svg>",
        encoding="utf-8",
    )
    # El dominio se activa solo cuando el DNS de juanchica.com ya apunte a GitHub Pages.
    if SITIO.get("dominio_activo"):
        (SALIDA / "CNAME").write_text(SITIO["dominio"] + "\n", encoding="utf-8")
    (SALIDA / ".nojekyll").write_text("", encoding="utf-8")

    # Portada
    proyectos = "".join(
        (f'<a class="proyecto" href="{e(p["url"])}">' if p.get("url") else '<div class="proyecto">')
        + f'<h3>{e(p["nombre"])}</h3><p>{e(p["texto"])}</p>'
        + (f'<span class="ir">{e(p["enlace"])} →</span>' if p.get("url") and p.get("enlace") else "")
        + ("</a>" if p.get("url") else "</div>")
        for p in SITIO["proyectos"]
    )
    portada = f"""<main>
<section class="hero"><div class="columna">
  {ISOTIPO}
  <h1>juanchica<span class="dom">.com</span></h1>
  <hr class="regla">
  <p class="temas">{e(SITIO['temas'])}</p>
  <p class="bio">{e(SITIO['bio'])}</p>
</div></section>
<section class="seccion"><div class="contenedor">
  <p class="etiqueta">En qué estoy</p>
  <div class="proyectos">{proyectos}</div>
</div></section>
<section class="seccion"><div class="columna">
  <p class="etiqueta">Blog</p>
  {lista(entradas, 5).replace('{raiz}', '')}
  {'<a class="volver" href="blog/">Ver todas las entradas →</a>' if len(entradas) > 5 else ''}
</div></section>
</main>"""
    (SALIDA / "index.html").write_text(
        pagina("juanchica", SITIO["bio"], portada, "assets/estilos.css", ""), encoding="utf-8")

    # Blog
    (SALIDA / "blog").mkdir()
    indice = f"""<main class="entrada"><div class="columna">
  <p class="etiqueta">Blog</p>
  {lista(entradas).replace('{raiz}', '../')}
</div></main>"""
    (SALIDA / "blog" / "index.html").write_text(
        pagina("Blog · juanchica", "Entradas de juanchica.com", indice, "../assets/estilos.css", "../"), encoding="utf-8")

    for x in entradas:
        d = SALIDA / "blog" / x["slug"]
        d.mkdir()
        cuerpo = f"""<main class="entrada"><article class="columna">
  <p class="meta">{fecha_larga(x['fecha'])}</p>
  <h1>{e(x['titulo'])}</h1>
  {f'<p class="bajada">{e(x["bajada"])}</p>' if x['bajada'] else ''}
  <div class="cuerpo">{x['html']}</div>
  <a class="volver" href="../">← Todas las entradas</a>
</article></main>"""
        (d / "index.html").write_text(
            pagina(f"{x['titulo']} · juanchica", x["bajada"] or x["titulo"], cuerpo, "../../assets/estilos.css", "../../"),
            encoding="utf-8")

    print(f"Listo: portada + blog con {len(entradas)} entrada(s) publicadas en docs/")


if __name__ == "__main__":
    construir()

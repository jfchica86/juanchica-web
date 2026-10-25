# juanchica.com

Página personal de Juan Francisco Chica: portada, blog y el botón **Entrar** a las apps.
🟢 Personal. Marca: guía de identidad juanchica (2026) — Hanken Grotesk; Tinta #1B1A17,
Piedra #6E685D, Tierra #C9BBA6, Crudo #F2EEE6.

## Cómo se publica una entrada
1. Escribir `contenido/entradas/AAAA-MM-DD-slug.md` con la cabecera (`titulo`, `fecha`, `bajada`,
   `publicada: si`). Sin `publicada: si` queda como borrador y no sale.
2. `python3 construir.py` (requiere `pip install markdown`). Genera `docs/`.
3. Commit y push: GitHub Pages publica `docs/` de `main`.

## Dónde vive cada cosa
| Qué | Dónde |
|---|---|
| Texto de portada, bio, proyectos, enlace de apps | `sitio.json` |
| Diseño | `plantilla/estilos.css` · símbolo en `plantilla/isotipo.svg` |
| Entradas | `contenido/entradas/` |
| Sitio generado (no editar a mano) | `docs/` |

## Dominio
`juanchica.com` → GitHub Pages: poner `"dominio_activo": true` en `sitio.json` y reconstruir cuando el DNS ya apunte (eso crea `docs/CNAME`). Las apps quedan en `app.juanchica.com` → Render
(`juanchica-portal`). Mientras el DNS no cambie, el botón Entrar apunta a
`juanchica-portal.onrender.com/login` (`apps_url` en `sitio.json`).

## Inglés y audio (desde 2026-10-25)
- Versión en inglés en `/en/`: textos de portada en `sitio.json` → `en`; páginas en `contenido/en/paginas/`
  (`about.md` es la pareja de `sobre-mi.md`, ver `PAGINAS_EN` en `construir.py`); entradas en
  `contenido/en/entradas/` con el **mismo nombre de archivo** que la española. El botón ES · EN lleva
  a la pareja; si no existe, a la portada del otro idioma.
- Audio con la voz de Juan (ElevenLabs Studio, a mano): el MP3 se comprime con
  `afconvert -f m4af -d aac -b 64000 entrada.mp3 contenido/audio/<slug>.m4a` y el reproductor
  aparece solo en la entrada en español.

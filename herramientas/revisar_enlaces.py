"""Revisa el catálogo de cursos: formato de las tablas y que cada enlace responda.

Uso:
    python herramientas/revisar_enlaces.py              revisa formato y enlaces (necesita internet)
    python herramientas/revisar_enlaces.py --sin-red    solo formato (lo que corre el CI en cada PR)
    python herramientas/revisar_enlaces.py otro.md      revisa otro archivo en vez de README.md

Solo usa la biblioteca estándar de Python (3.9 o más nuevo).
Sale con 0 si todo está bien y con 1 si hay algo que corregir.
"""
import argparse
import concurrent.futures
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

ENCABEZADO = ["Curso", "Plataforma", "Idioma", "Nivel", "Horas", "Certificado gratis"]
IDIOMAS = {"EN", "ES"}
NIVELES = {"Principiante", "Intermedio", "Avanzado", "Todos los niveles"}
CERTIFICADO = {"Sí", "No", "Insignia"}
HORAS = re.compile(r"^(~?\d+(\.\d+)?|\d+ a \d+|<1|Variable)$")
ENLACE = re.compile(r"^\[([^\]]+)\]\((\S+)\)$")
ACORTADORES = {
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "cutt.ly", "rebrand.ly",
    "shorturl.at", "is.gd", "buff.ly", "rb.gy", "lnkd.in",
}
PARAMETROS_AFILIADO = {"ref", "aff", "affiliate", "affid", "aff_id", "ranmid", "ranEAID", "ransiteid", "couponcode"}
AGENTE = "Mozilla/5.0 (compatible; revisar-enlaces/1.0; catalogo cursos-gratis)"


def celdas(linea):
    return [c.strip() for c in linea.strip().strip("|").split("|")]


def leer_tablas(texto):
    """Devuelve (filas, errores). Cada fila: (num_linea, ruta, celdas)."""
    filas, errores = [], []
    lineas = texto.splitlines()
    ruta = None
    i = 0
    while i < len(lineas):
        linea = lineas[i]
        if linea.startswith("## "):
            ruta = linea[3:].strip()
        if linea.lstrip().startswith("|") and celdas(linea)[0] == "Curso":
            if celdas(linea) != ENCABEZADO:
                errores.append(f"línea {i + 1}: el encabezado debe ser | {' | '.join(ENCABEZADO)} |")
            sep = lineas[i + 1] if i + 1 < len(lineas) else ""
            if not re.fullmatch(r"\|(\s*:?-{3,}:?\s*\|){6}", sep.strip()):
                errores.append(f"línea {i + 2}: falta la fila separadora de 6 columnas (|---|---|...)")
            i += 2
            while i < len(lineas) and lineas[i].lstrip().startswith("|"):
                filas.append((i + 1, ruta, celdas(lineas[i])))
                i += 1
            continue
        i += 1
    return filas, errores


def revisar_fila(num, c):
    errores = []
    if len(c) != 6:
        return [f"línea {num}: tiene {len(c)} columnas y deben ser 6"], None
    curso, plataforma, idioma, nivel, horas, cert = c
    m = ENLACE.match(curso)
    if not m:
        return [f"línea {num}: la columna Curso debe ser un enlace [nombre](https://...)"], None
    url = m.group(2)
    partes = urllib.parse.urlsplit(url)
    if partes.scheme != "https":
        errores.append(f"línea {num}: el enlace debe usar https")
    host = partes.netloc.lower().removeprefix("www.")
    if host in ACORTADORES:
        errores.append(f"línea {num}: no se aceptan acortadores ({host}); poné el enlace oficial")
    params = {k.lower() for k in urllib.parse.parse_qs(partes.query)}
    if params & {p.lower() for p in PARAMETROS_AFILIADO}:
        errores.append(f"línea {num}: el enlace trae parámetros de afiliado; quitáselos")
    if not plataforma:
        errores.append(f"línea {num}: falta la plataforma")
    if not idioma or any(x.strip() not in IDIOMAS for x in idioma.split(",")):
        errores.append(f"línea {num}: Idioma debe ser EN, ES o 'EN, ES' (dice '{idioma}')")
    if nivel not in NIVELES:
        errores.append(f"línea {num}: Nivel debe ser uno de {sorted(NIVELES)} (dice '{nivel}')")
    if not HORAS.match(horas):
        errores.append(f"línea {num}: Horas debe ser un número, ~número, 'N a M', '<1' o 'Variable' (dice '{horas}')")
    if cert not in CERTIFICADO:
        errores.append(f"línea {num}: Certificado gratis debe ser Sí, No o Insignia (dice '{cert}')")
    return errores, url


def probar(url, intentos=2):
    """Devuelve None si responde 200 en su página, o el motivo del fallo."""
    motivo = None
    for _ in range(intentos):
        try:
            pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept": "text/html,*/*"})
            with urllib.request.urlopen(pedido, timeout=25) as r:
                final = r.geturl()
                if r.status != 200:
                    return f"respondió {r.status}"
                antes, despues = urllib.parse.urlsplit(url), urllib.parse.urlsplit(final)
                if despues.path in ("", "/") and antes.path not in ("", "/"):
                    return f"redirige a la portada ({final}); el curso pudo haberse retirado"
                if re.search(r"search|notfound", despues.path + despues.query, re.I) and not re.search(
                    r"search|notfound", antes.path + antes.query, re.I
                ):
                    return f"redirige a una búsqueda ({final}); el curso pudo haberse retirado"
                return None
        except urllib.error.HTTPError as e:
            motivo = f"respondió {e.code}"
            if e.code in (404, 410):
                break
        except Exception as e:  # noqa: BLE001 (red caída, tiempo agotado, certificado)
            motivo = f"no responde ({e.__class__.__name__})"
    return motivo


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # para que las tildes se vean bien en Windows
    p =argparse.ArgumentParser(description="Revisa formato y enlaces del catálogo de cursos.")
    p.add_argument("archivo", nargs="?", default=str(RAIZ / "README.md"))
    p.add_argument("--sin-red", action="store_true", help="solo revisa el formato, sin abrir los enlaces")
    a = p.parse_args()

    texto = Path(a.archivo).read_text(encoding="utf-8")
    filas, errores = leer_tablas(texto)
    if not filas:
        errores.append("no encontré ninguna tabla de cursos")

    vistos = {}
    urls = []
    for num, _ruta, c in filas:
        errs, url = revisar_fila(num, c)
        errores += errs
        if url:
            if url in vistos:
                errores.append(f"línea {num}: el enlace se repite (ya está en la línea {vistos[url]})")
            else:
                vistos[url] = num
                urls.append((num, url))

    if not a.sin_red and urls:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            resultados = list(ex.map(lambda nu: (nu[0], nu[1], probar(nu[1])), urls))
        for num, url, motivo in resultados:
            if motivo:
                errores.append(f"línea {num}: {url} {motivo}")

    rutas = {r for _, r, _ in filas}
    modo = "formato" if a.sin_red else "formato y enlaces"
    if errores:
        print(f"Revisé {len(filas)} cursos en {len(rutas)} rutas ({modo}). Hay {len(errores)} cosas que corregir:")
        for e in errores:
            print(f"  {e}")
        return 1
    print(f"Todo bien: {len(filas)} cursos en {len(rutas)} rutas ({modo}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

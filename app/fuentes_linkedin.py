"""
Colector de LinkedIn Jobs mediante su API pública de invitado.

LinkedIn bloquea la búsqueda normal con un muro de autenticación, pero expone
`/jobs-guest/jobs/api/seeMoreJobPostings/search`, que devuelve las tarjetas de
resultados en HTML sin necesidad de sesión. Eso permite incluir la bolsa más
grande del mercado sin pedirle al usuario que inicie sesión ni manejar sus
credenciales.

Filtros de LinkedIn que se usan:
  f_E=1  -> Prácticas (internship)
  f_E=2  -> Nivel inicial (entry level)
  f_WT=2 -> Remoto
  f_TPR  -> publicadas en el último periodo
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor

from bs4 import BeautifulSoup

from nucleo import log, obtener_texto, obtener_texto_cache, vacante

BASE = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

# (palabras clave, ubicacion, filtros extra)
BUSQUEDAS = [
    # --- Monterrey presencial ---
    ("ciberseguridad", "Monterrey, Nuevo Leon, Mexico", "&f_E=1%2C2"),
    ("seguridad informatica", "Monterrey, Nuevo Leon, Mexico", "&f_E=1%2C2"),
    ("practicante sistemas", "Monterrey, Nuevo Leon, Mexico", ""),
    ("becario tecnologia", "Monterrey, Nuevo Leon, Mexico", ""),
    ("cybersecurity", "Monterrey, Nuevo Leon, Mexico", "&f_E=1%2C2"),
    ("SOC analyst", "Monterrey, Nuevo Leon, Mexico", "&f_E=1%2C2"),
    ("inteligencia artificial", "Monterrey, Nuevo Leon, Mexico", "&f_E=1%2C2"),
    ("data science", "Monterrey, Nuevo Leon, Mexico", "&f_E=1%2C2"),
    ("riesgos tecnologia", "Monterrey, Nuevo Leon, Mexico", "&f_E=1%2C2"),
    ("auditoria de sistemas", "Monterrey, Nuevo Leon, Mexico", "&f_E=1%2C2"),
    # --- Mexico nacional (remoto e hibrido) ---
    ("ciberseguridad", "Mexico", "&f_E=1%2C2&f_WT=2"),
    ("cybersecurity intern", "Mexico", "&f_WT=2"),
    ("GRC analyst", "Mexico", "&f_E=1%2C2"),
    ("seguridad de la informacion", "Mexico", "&f_E=1%2C2"),
    ("AI safety", "Mexico", "&f_WT=2"),
    # --- Remoto global abierto a LatAm ---
    ("cybersecurity internship", "Latin America", "&f_WT=2"),
    ("security analyst latam", "Worldwide", "&f_WT=2&f_E=1%2C2"),
    ("AI red team", "Worldwide", "&f_WT=2"),
    ("trust and safety", "Latin America", "&f_WT=2&f_E=1%2C2"),
    ("prompt engineer", "Latin America", "&f_WT=2"),
    ("security intern remote", "Worldwide", "&f_WT=2&f_E=1%2C2"),
    # --- Ampliacion del barrido ---
    ("becario", "Monterrey, Nuevo Leon, Mexico", "&f_E=1"),
    ("practicante", "Monterrey, Nuevo Leon, Mexico", "&f_E=1"),
    ("intern", "Monterrey, Nuevo Leon, Mexico", "&f_E=1"),
    # 'trainee' se anadio el 29-ago-2026. Es la palabra MAS frecuente en los
    # titulos de vacantes de practicas de seguridad (14,5% de 69, medido con
    # tiene_termino sobre la base), por delante de 'practicante' (13,0%) y
    # 'becario' (8,7%) -- y era la unica de las tres que NO se buscaba aqui.
    # Llegaban 16 de LinkedIn por el filtro f_E, nunca por palabra clave;
    # 'practicante', que si se busca, traia 74. El clasificador ya las
    # reconocia bien (las 69 salen como nivel='practicas'): el hueco estaba
    # en ir a buscarlas, no en entenderlas.
    ("trainee", "Monterrey, Nuevo Leon, Mexico", "&f_E=1"),
    ("soporte tecnico", "Monterrey, Nuevo Leon, Mexico", "&f_E=1%2C2"),
    ("infraestructura TI", "Monterrey, Nuevo Leon, Mexico", "&f_E=1%2C2"),
    ("analista de datos", "Monterrey, Nuevo Leon, Mexico", "&f_E=1%2C2"),
    ("SOC", "Monterrey, Nuevo Leon, Mexico", ""),
    ("SIEM", "Mexico", "&f_E=1%2C2"),
    ("ISO 27001", "Mexico", "&f_E=1%2C2"),
    ("auditoria de sistemas", "Mexico", "&f_E=1%2C2"),
    ("cumplimiento normativo TI", "Mexico", "&f_E=1%2C2"),
    ("identity access management", "Mexico", "&f_E=1%2C2"),
    ("incident response", "Mexico", "&f_E=1%2C2"),
    ("vulnerability management", "Mexico", "&f_E=1%2C2"),
    ("becario ciberseguridad", "Mexico", ""),
    ("practicante ciberseguridad", "Mexico", ""),
    ("trainee ciberseguridad", "Mexico", ""),
    ("trainee tecnologia", "Mexico", "&f_E=1"),
    ("cybersecurity analyst", "Mexico", "&f_E=1%2C2"),
    ("information security", "Mexico", "&f_E=1%2C2"),
    ("data analyst", "Mexico", "&f_E=1%2C2&f_WT=2"),
    ("machine learning", "Mexico", "&f_E=1%2C2&f_WT=2"),
    # Remoto abierto a LatAm
    ("security engineer", "Latin America", "&f_WT=2&f_E=1%2C2"),
    ("SOC analyst", "Latin America", "&f_WT=2&f_E=1%2C2"),
    ("GRC", "Latin America", "&f_WT=2"),
    ("compliance analyst", "Latin America", "&f_WT=2&f_E=1%2C2"),
    ("data annotation", "Worldwide", "&f_WT=2"),
    ("AI evaluator", "Worldwide", "&f_WT=2"),
    ("red teaming AI", "Worldwide", "&f_WT=2"),
    ("LLM security", "Worldwide", "&f_WT=2"),
    ("junior security", "Worldwide", "&f_WT=2&f_E=1%2C2"),
    ("entry level cybersecurity", "Worldwide", "&f_WT=2&f_E=1%2C2"),
]

PAGINAS = 10  # LinkedIn devuelve 25 tarjetas por página: 250 por búsqueda


def _una(keywords: str, location: str, extra: str, inicio: int) -> list[dict]:
    url = (
        f"{BASE}?keywords={keywords.replace(' ', '%20')}"
        f"&location={location.replace(' ', '%20').replace(',', '%2C')}"
        f"&start={inicio}{extra}"
    )
    codigo, html = obtener_texto(url, timeout=20)
    if codigo != 200 or "base-card" not in html:
        return []

    sopa = BeautifulSoup(html, "lxml")
    salida = []
    for card in sopa.select("div.base-card, li div.base-search-card"):
        urn = card.get("data-entity-urn", "")
        id_li = urn.split(":")[-1] if urn else ""

        t = card.select_one("h3.base-search-card__title")
        e = card.select_one("h4.base-search-card__subtitle")
        u = card.select_one("span.job-search-card__location")
        a = card.select_one("a.base-card__full-link") or card.select_one("a")
        fecha = card.select_one("time")

        titulo = t.get_text(strip=True) if t else ""
        if not titulo:
            continue

        enlace = (a.get("href", "") if a else "").split("?")[0]
        if not enlace and id_li:
            enlace = f"https://www.linkedin.com/jobs/view/{id_li}/"

        salida.append(
            vacante(
                titulo=titulo,
                empresa=e.get_text(strip=True) if e else "",
                url=enlace,
                fuente="linkedin",
                ubicacion=u.get_text(strip=True) if u else location,
                descripcion="",  # el detalle exige sesión; se enriquece al abrir
                publicado=(fecha.get("datetime") if fecha else ""),
                extra={"id_linkedin": id_li, "consulta": f"{keywords} @ {location}"},
            )
        )
    return salida


DETALLE = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{}"

# Huellas de cierre en la ficha de invitado de LinkedIn.
CERRADA = (
    "no longer accepting applications",
    "ya no acepta solicitudes",
    "esta oferta ya no",
)

# Texto de la INTERFAZ de LinkedIn, no del anuncio: el aviso de cookies, el
# formulario de acceso y la publicidad de sus funciones de IA.
#
# El fallo que lo hizo necesario. "Practicante de Rentabilidad" de DEACERO
# aparecio recomendada con 69 puntos como vacante de TI. Su descripcion real
# no dice nada de TI; las tres "señales tecnicas" que la ascendieron salian de
# la propia pagina de LinkedIn: "Usa la IA para evaluar como encajarias",
# "Obten consejos de la IA", "Inicia sesion", "Email o telefono". Afectaba a
# 430 descripciones, y a 107 vacantes cuya area se decidio SOLO por ese texto:
# mantenimiento, mecatronica, tool room, activos fijos.
# CUIDADO AL EDITAR ESTO. La primera version usaba `.*?(?=\n|$)` con DOTALL
# para cortar "hasta el final de la linea". Pero `nucleo.limpiar_html` colapsa
# todos los espacios con `\s+`, asi que **el texto no tiene ni un salto de
# linea**: el unico anclaje posible era `$`, y cada alternativa se comio la
# descripcion entera hasta el final. Como esas frases estan al PRINCIPIO de la
# ficha de LinkedIn, destruyo 607 descripciones: la mediana paso de 3.306 a 76
# caracteres, y 42 vacantes legitimas perdieron puntos al desaparecer el texto
# donde estaban sus habilidades.
#
# Regla para no repetirlo: **ninguna alternativa lleva comodin abierto**. Todo
# va con frases literales o con un limite explicito de caracteres.
INTERFAZ = re.compile(
    r"(usa la ia para evaluar c[oó]mo encajar[ií]as"
    r"|obt[eé]n consejos de la ia sobre este empleo[^.]{0,40}"
    r"|personaliza mi curr[ií]culum"
    r"|inicia sesi[oó]n para acceder a (los )?consejos de la ia"
    r"|¿encajar[ií]a bien en este puesto\?"
    r"|email o tel[eé]fono|¿has olvidado tu contrase[nñ]a\??"
    r"|descubre a qui[eé]n ha contratado[^.]{0,60}?para este puesto"
    r"|s[eé] de los primeros \d+ solicitantes"
    r"|\b\d+ solicitudes\b"
    r"|solicitar guardar denunciar este empleo"
    r"|denunciar este empleo"
    r"|al hacer clic en .continuar.[^.]{0,120}"
    r")", re.I)


def quitar_interfaz(texto: str) -> str:
    """Deja solo el anuncio, sin el texto de la pagina que lo envuelve.

    Salvaguarda: si la limpieza se lleva mas de la mitad del texto, algo va mal
    en el patron y se devuelve el original. Es preferible dejar algo de basura
    que borrar el anuncio, porque sin descripcion el scoring se queda ciego.
    """
    limpio = re.sub(r"\s{2,}", " ", INTERFAZ.sub(" ", texto)).strip()
    if len(texto) > 400 and len(limpio) < len(texto) * 0.5:
        return texto
    return limpio


def enriquecer(v: dict) -> dict:
    """Descarga la descripción completa y de paso verifica que siga abierta.

    La tarjeta de resultados no trae descripción, y sin descripción el scoring
    se queda ciego: no puede ver ni las habilidades ni las restricciones
    geográficas. La ficha de invitado sí la trae y no exige sesión.
    """
    # El texto de la propia interfaz se cuela en la descripción y el
    # clasificador lo lee como si fuera el anuncio. Ver `quitar_interfaz`.
    jid = v.get("extra", {}).get("id_linkedin")
    if not jid:
        return v
    codigo, html = obtener_texto_cache(DETALLE.format(jid), timeout=20)
    if codigo != 200:
        v["verificacion"] = {
            "estado": "sin-verificar", "metodo": "linkedin-guest",
            "detalle": f"la ficha respondio HTTP {codigo}", "http": codigo,
            "fecha": __import__("nucleo").ahora_iso(), "url_final": v["url"],
        }
        return v

    from nucleo import ahora_iso, limpiar_html

    texto = limpiar_html(html)
    bajo = texto.lower()
    cerrada = next((h for h in CERRADA if h in bajo), None)
    v["descripcion"] = quitar_interfaz(texto)[:6000]
    v["verificacion"] = {
        "estado": "cerrada" if cerrada else "viva",
        "metodo": "linkedin-guest",
        "detalle": (f"huella: '{cerrada}'" if cerrada
                    else "la ficha publica devuelve la vacante y admite postulacion"),
        "http": 200,
        "fecha": ahora_iso(),
        "url_final": v["url"],
    }
    return v


def recolectar_todo(hilos: int = 10, con_detalle: bool = True) -> list[dict]:
    tareas = []
    with ThreadPoolExecutor(max_workers=hilos) as ex:
        for kw, loc, extra in BUSQUEDAS:
            for pagina in range(PAGINAS):
                tareas.append(ex.submit(_una, kw, loc, extra, pagina * 25))
        salida = []
        for f in tareas:
            try:
                salida.extend(f.result())
            except Exception:
                pass

    if not con_detalle:
        return salida

    # Deduplicar por id antes de pedir detalles: la misma vacante sale en
    # varias búsquedas y no tiene sentido descargarla más de una vez.
    unicas: dict[str, dict] = {}
    for v in salida:
        jid = v.get("extra", {}).get("id_linkedin") or v["id"]
        unicas.setdefault(jid, v)

    lista = list(unicas.values())
    log(f"  linkedin: {len(salida)} tarjetas -> {len(lista)} unicas, descargando fichas...")
    with ThreadPoolExecutor(max_workers=hilos) as ex:
        lista = list(ex.map(enriquecer, lista))
    return lista


if __name__ == "__main__":
    vs = recolectar_todo()
    log(f"LINKEDIN: {len(vs)} vacantes crudas")
    vistos = set()
    for v in vs:
        clave = (v["titulo"], v["empresa"])
        if clave in vistos:
            continue
        vistos.add(clave)
        if len(vistos) > 22:
            break
        print(f"  - {v['titulo'][:52]:52} | {v['empresa'][:26]:26} | {v['ubicacion'][:30]}")

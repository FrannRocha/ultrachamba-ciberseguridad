"""
Generador de correos de postulación adaptados a cada vacante.

Por qué existe. El sistema ya encuentra las vacantes buenas, pero hasta ahora
El usuario tenía que escribir cada correo a mano. Las plantillas de
`guias/correos-de-postulacion.md` son buenas, pero son genéricas: un correo que
no nombra la vacante concreta ni cruza el CV con lo que esa vacante pide se lee
como un envío masivo y se borra.

Qué hace este módulo. Toma una vacante ya analizada (la fila de SQLite, con su
área, su ubicación, sus años exigidos y las habilidades que coincidieron con el
CV) y devuelve un correo listo para revisar, más una lista de advertencias
honestas para que él decida si vale la pena mandarlo.

Las cuatro reglas de redacción vienen de la guía y NO son negociables:

  1. El asunto dice quién es y qué quiere, con un hecho concreto.
  2. La primera línea es un hecho verificable, no una presentación.
  3. Un solo pedido al final, respondible con sí o no.
  4. Nada de "Espero que se encuentre bien".

Y una regla de honestidad que pesa más que todas: aquí no se inventa nada. Las
habilidades que se mencionan salen del cruce entre `perfil.HABILIDADES` y las
que la vacante pidió; lo que tu perfil respalda con un entregable se escribe
como "lo hice" y lo que solo está en estudio se escribe como lo que es. Una
certificación EN PREPARACIÓN nunca se presenta como obtenida.

IMPORTANTE. Las aperturas (`ANGULOS`) y las frases de `CONCEPTOS` vienen como
EJEMPLO a propósito: son plantillas, no logros de nadie. Rellena tu perfil y
reescríbelas con lo tuyo antes de enviar un solo correo. Un correo que afirma
un logro ajeno te quema con quien lo lee.

Uso:
    from generador_correos import generar, generar_por_id, generar_lote
    correo = generar_por_id("d9b05814e7e1fc17")
    print(correo["asunto"]); print(correo["cuerpo"]); print(correo["avisos"])
"""
from __future__ import annotations

import json
import re
import sys
import textwrap
import unicodedata
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from almacen import conexion, consultar  # noqa: E402
from nucleo import normalizar, tiene_termino  # noqa: E402
from perfil import (  # noqa: E402
    AMM,
    CANDIDATO,
    ESTADOS_EEUU,
    HABILIDADES,
    LOGROS,
    LOGROS_EN,
    NIVEL_EXCLUIR,
    PAISES_CERRADOS,
    ROL_NO_TECNICO,
    UBIC_EXTRANJERA,
    UBIC_MX_OTRA,
)

ANCHO = 78  # ancho de línea del cuerpo: se lee igual en móvil y en escritorio
AREAS = ("ciber-ia", "ciberseguridad", "ia", "ti-general")


# ------------------------------------------------------------------ texto ----

def _normalizar(texto: str) -> str:
    """Minúsculas sin acentos.

    Se reimplementa aquí en lugar de importar `nucleo.normalizar` porque
    `nucleo` arrastra `requests` y toda la pila de red: redactar un correo no
    debería depender de que las librerías HTTP estén instaladas.
    """
    nfkd = unicodedata.normalize("NFKD", (texto or "").lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# Cromo de LinkedIn. Aparece en español en TODA ficha recogida desde
# mx.linkedin.com, incluso cuando el puesto está escrito en inglés, así que si
# no se quita antes de contar palabras el detector de idioma dice "español"
# para vacantes de San Francisco.
_BOILERPLATE = [
    "descubre a quien ha contratado", "unete o inicia sesion",
    "solicitar empleo de", "email o telefono", "contrasena mostrar",
    "has olvidado tu contrasena", "iniciar sesion con el email",
    "estas empezando a usar linkedin", "unete ahora",
    "al hacer clic en", "condiciones de uso", "politica de privacidad",
    "politica de cookies", "denunciar este empleo", "guardar denunciar",
    "se de los primeros", "solicitudes", "solicitar guardar",
    "enviar mensaje directo al anunciante", "iniciar sesion",
    "encontrar tu siguiente empleo", "para este puesto", "hace 1 dia",
    "sign in to", "join now", "your job alert is set", "show more",
    "by clicking continue", "user agreement", "privacy policy",
    "cookie policy", "report this job", "be among the first",
]

_ES_MARCADORES = (
    "que|de|la|el|los|las|del|para|con|por|una|unos|como|mas|este|esta|al|se|"
    "su|sus|nuestro|nuestra|experiencia|conocimientos|empresa|puesto|"
    "actividades|requisitos|ofrecemos|funciones|carrera|sueldo|prestaciones|"
    "horario|licenciatura|ingenieria|deseable|manejo|apoyo|seguimiento|"
    "buscamos|responsabilidades|habilidades|estudios|titulo|zona|anos"
)
_EN_MARCADORES = (
    "the|and|with|for|you|your|our|we|will|are|have|this|that|from|about|"
    "team|role|experience|requirements|responsibilities|skills|work|across|"
    "including|who|what|strong|ability|years|looking|join|help|build|"
    "please|preferred|qualifications|benefits|opportunity"
)
_RX_ES = re.compile(rf"\b(?:{_ES_MARCADORES})\b")
_RX_EN = re.compile(rf"\b(?:{_EN_MARCADORES})\b")

_RX_MX_OTRA = re.compile(UBIC_MX_OTRA)
_RX_EXTRANJERA = re.compile(UBIC_EXTRANJERA)
_RX_HISPANO = re.compile(
    r"\b(mexico|colombia|chile|argentina|peru|espana|spain|uruguay|paraguay|"
    r"bolivia|ecuador|venezuela|guatemala|honduras|salvador|nicaragua|"
    r"costa rica|panama|republica dominicana|puerto rico|latam|latinoamerica)\b"
)

# "mexico" a secas también casa dentro de "New Mexico", que es un estado de
# Estados Unidos. Sin el lookbehind, "Remote - New Mexico, USA" se leía como
# vacante mexicana y se contestaba en español.
_RX_MEXICO = re.compile(r"(?<!new )\bmexico\b")

# Países no hispanohablantes. Importan cuando aparecen JUNTO a México en la
# ubicación ("U.S. or Mexico Remote"): ahí la requisición la lleva el equipo de
# allá y quien lee el correo trabaja en inglés.
_RX_ANGLO = re.compile(
    r"\bu\.s\.|\bus\b|\busa\b|\bunited states\b|\bcanada\b|\buk\b|"
    r"\bunited kingdom\b|\bengland\b|\bireland\b|\baustralia\b|"
    r"\bnew zealand\b|\bindia\b|\bsingapore\b|\bgermany\b|\bdeutschland\b|"
    r"\bnetherlands\b|\bfrance\b|\bpoland\b|\bisrael\b|\bjapan\b|\bchina\b|"
    r"\bemea\b|\bapac\b"
)

# Fuentes cuyo catálogo es mexicano: si la vacante viene de ahí, la escribió
# alguien que trabaja en español aunque el título esté en inglés.
_FUENTES_MX = ("occ", "computrabajo", "empleos", "bumeran", "indeed-mx")

# Vocabulario de TÍTULO. Solo decide cuando la vacante no trae ubicación, que
# es justo el caso de los tableros extranjeros (Ashby, Greenhouse, portales
# alemanes): ahí el título es la única señal que hay.
# Ojo: aquí NO va "auditor", que se escribe igual en inglés y empujaba a
# español fichas como "IT Auditor (all genders)" de un banco austriaco.
_ES_TITULO = (
    "practicante|becario|becaria|ingeniero|ingeniera|analista|especialista|"
    "consultor|consultora|desarrollador|desarrolladora|tecnico|jefe|gerente|"
    "seguridad|informacion|sistemas|datos|redes|soporte|auditoria|"
    "riesgos|calidad|servicio|atencion|gestion|administracion|"
    "licenciatura|residente|practicas|empresa|nuestro|para"
)
# 'werkstudent', 'praktikum' y compañía son alemanas: no son español, y a una
# empresa alemana se le escribe en inglés.
_EN_TITULO = (
    "intern|internship|student|engineer|analyst|specialist|consultant|"
    "developer|manager|security|information|systems|network|support|audit|"
    "risk|quality|service|governance|compliance|associate|graduate|trainee|"
    "apprentice|summer|fall|winter|spring|senior|junior|lead|officer|"
    "scientist|architect|program|assistant|coordinator|advisor|technology|"
    "werkstudent|werkstudentin|praktikum|abschlussarbeit|stellentitel|titel"
)
_RX_ES_TITULO = re.compile(rf"\b(?:{_ES_TITULO})\b")
_RX_EN_TITULO = re.compile(rf"\b(?:{_EN_TITULO})\b")

# Ortografía que solo existe en español. Se mira sobre el texto SIN normalizar.
_RX_ORTOGRAFIA_ES = re.compile(r"[ñáéíóúü¿¡]", re.I)

# Francés y alemán también llevan acentos y diéresis, así que la señal de
# ortografía por sí sola marcaba como españolas vacantes de Ippon ("Data
# Engineer (H/F)") y de universidades duales alemanas. A esas se les escribe en
# inglés, no en español.
_RX_OTRO_IDIOMA = re.compile(
    r"\(h/f\)|\(f/h\)|\bh/f\b|\(m/w/d\)|\(w/m/d\)|\bm/w/d\b|"
    r"\bingenieur|\bchef\(?fe\)? de projet|\bstage\b|\balternance\b|"
    r"\bcdi\b|\bcdd\b|\bduales studium\b|\bkunstliche\b|\bwerkstudent|"
    r"\bpraktikum\b|\babschlussarbeit\b|\bstellentitel\b|\bmitarbeiter|"
    r"\bausbildung\b|\bund\b|\bder\b|\bdie\b|\bmit\b|\bfur\b|"
    r"\bnous\b|\bvous\b|\bpour\b|\bavec\b"
)


def _sin_ruido(texto: str) -> str:
    """Texto normalizado y sin el cromo de los agregadores."""
    t = _normalizar(texto)
    for frase in _BOILERPLATE:
        t = t.replace(frase, " ")
    return re.sub(r"\s+", " ", t)


def _envolver(parrafo: str) -> str:
    return textwrap.fill(parrafo.strip(), width=ANCHO)


# ----------------------------------------------------------- la vacante ------

def _campo(v: dict, clave: str, por_defecto=""):
    valor = v.get(clave)
    return por_defecto if valor is None else valor


def _habilidades_de(v: dict) -> list[str]:
    """Las habilidades que el análisis cruzó con el CV, venga de donde venga.

    `consultar()` devuelve la lista ya deserializada en
    `habilidades_coincidentes`; una fila cruda de SQLite la trae como JSON en
    `habilidades`. Se aceptan las dos formas para que `generar()` funcione con
    cualquiera de las dos sin que quien llama tenga que saberlo.
    """
    crudo = v.get("habilidades_coincidentes")
    if crudo is None:
        crudo = v.get("habilidades")
    if isinstance(crudo, str):
        try:
            crudo = json.loads(crudo or "[]")
        except (ValueError, TypeError):
            crudo = []
    if not isinstance(crudo, list):
        return []
    # Filtro duro: si no está en perfil.py, no es una habilidad del usuario.
    return [str(h).strip().lower() for h in crudo if str(h).strip().lower() in HABILIDADES]


def _motivos_de(v: dict) -> list[str]:
    crudo = v.get("motivos")
    if isinstance(crudo, str):
        try:
            crudo = json.loads(crudo or "[]")
        except (ValueError, TypeError):
            crudo = []
    return list(crudo or [])


def _area_de(v: dict) -> str:
    """El área ya clasificada; si falta o es rara, se infiere del título."""
    area = str(_campo(v, "area")).strip().lower()
    if area in AREAS:
        return area
    texto = _sin_ruido(f"{_campo(v, 'titulo')} {_campo(v, 'descripcion')[:1500]}")
    hay_ciber = bool(re.search(
        r"\b(security|securit|cyber|ciber|seguridad|infosec|soc|siem|grc|"
        r"pentest|hardening|blue team|red team)", texto))
    hay_ia = bool(re.search(
        r"\b(ai|ia|ml|machine learning|inteligencia artificial|llm|prompt|"
        r"genai|alignment|deep learning)\b", texto))
    if hay_ciber and hay_ia:
        return "ciber-ia"
    if hay_ciber:
        return "ciberseguridad"
    if hay_ia:
        return "ia"
    return "ti-general"


def _en_monterrey(v: dict) -> bool:
    ubic = _normalizar(_campo(v, "ubicacion"))
    return any(m in ubic for m in AMM)


def _es_remota(v: dict) -> bool:
    if str(_campo(v, "modalidad")).lower() in ("remoto", "hibrido"):
        return True
    campo = _normalizar(f"{_campo(v, 'ubicacion')} {_campo(v, 'titulo')}")
    return bool(re.search(r"\bremot(e|o|a)\b|\banywhere\b|work from home", campo))


# ---------------------------------------------------------------- idioma -----

def detectar_idioma(v: dict) -> tuple[str, list[str]]:
    """Devuelve ('es'|'en', razones).

    Se combinan varias señales porque ninguna basta sola, pero NO pesan igual:

      - La ubicación manda. Una vacante en México la lee alguien que trabaja en
        español, aunque la ficha esté redactada en inglés porque la empresa es
        multinacional. Antes esta señal valía 4 puntos y la descripción valía
        5, así que 175 vacantes de Monterrey y CDMX salían en inglés: justo lo
        contrario de lo que dice la regla. Ahora México es decisivo.
      - La excepción es la ubicación mixta ("U.S. or Mexico Remote"): ahí la
        requisición la lleva el equipo de allá y se contesta en inglés.
      - El título solo decide cuando no hay ubicación, que es el caso de los
        tableros extranjeros.
      - Ante la duda se escribe en INGLÉS. Un correo en inglés a un reclutador
        mexicano se lee sin problema; uno en español a un reclutador que no
        habla español se va a la basura sin leerse. El riesgo no es simétrico.
    """
    puntos = {"es": 0.0, "en": 0.0}
    razones: list[str] = []

    ubic_n = _normalizar(_campo(v, "ubicacion"))
    en_mexico = bool(_en_monterrey(v) or _RX_MX_OTRA.search(ubic_n)
                     or _RX_MEXICO.search(ubic_n))
    tambien_anglo = bool(_RX_ANGLO.search(ubic_n))

    if en_mexico and not tambien_anglo:
        puntos["es"] += 9  # decisivo: supera a cualquier combinación de texto
        razones.append("ubicacion en Mexico")
    elif en_mexico and tambien_anglo:
        puntos["en"] += 3
        razones.append("ubicacion mixta Mexico/extranjero: la lleva el equipo de alla")
    elif _RX_HISPANO.search(ubic_n):
        puntos["es"] += 6
        razones.append("ubicacion en pais hispanohablante")
    elif _RX_EXTRANJERA.search(ubic_n) or tambien_anglo:
        puntos["en"] += 4
        razones.append("ubicacion en el extranjero")
    elif ubic_n.strip():
        puntos["en"] += 1.5
        razones.append("ubicacion sin senal de pais hispano")

    if str(_campo(v, "fuente")).split(":")[0] in _FUENTES_MX:
        puntos["es"] += 3
        razones.append("fuente de catalogo mexicano")

    titulo_crudo = _campo(v, "titulo")
    titulo_n = _sin_ruido(titulo_crudo)
    t_es = len(_RX_ES.findall(titulo_n)) + len(_RX_ES_TITULO.findall(titulo_n))
    t_en = len(_RX_EN.findall(titulo_n)) + len(_RX_EN_TITULO.findall(titulo_n))
    puntos["es"] += min(3.0, t_es * 1.5)
    puntos["en"] += min(3.0, t_en * 1.5)
    if t_es or t_en:
        razones.append(f"titulo ({t_es} es / {t_en} en)")

    desc_n = _sin_ruido(_campo(v, "descripcion"))[:6000]

    # Francés y alemán se descartan ANTES de contar marcadores. El francés
    # comparte con el español las dos palabras más frecuentes de la lista
    # ("de", "la"), así que una ficha de Ippon en francés puntuaba 70 a 6 a
    # favor del español y salía un correo en español para Francia.
    otro_idioma = bool(_RX_OTRO_IDIOMA.search(f"{titulo_n} {desc_n[:1200]}"))
    hispano = bool(en_mexico or _RX_HISPANO.search(ubic_n))

    if otro_idioma and not hispano:
        puntos["en"] += 6
        razones.append("ficha en frances o aleman: se responde en ingles")
    else:
        d_es, d_en = len(_RX_ES.findall(desc_n)), len(_RX_EN.findall(desc_n))
        if d_es + d_en >= 12:
            if d_es > d_en * 1.3:
                puntos["es"] += 5
                razones.append(f"descripcion en espanol ({d_es} vs {d_en} marcadores)")
            elif d_en > d_es * 1.3:
                puntos["en"] += 5
                razones.append(f"descripcion en ingles ({d_en} vs {d_es} marcadores)")
            else:
                razones.append(f"descripcion mezclada ({d_es} es / {d_en} en)")
        # Ortografía que solo existe en español, sobre el texto sin normalizar.
        # Es el último recurso cuando no hay ni ubicación ni descripción.
        if _RX_ORTOGRAFIA_ES.search(
                f"{titulo_crudo} {_campo(v, 'descripcion')[:600]}"):
            puntos["es"] += 1.5
            razones.append("ortografia espanola (acentos o enes)")

    # Empate = sin evidencia. Se va a inglés por el riesgo asimétrico.
    idioma = "es" if puntos["es"] > puntos["en"] else "en"
    razones.append(f"puntaje es={puntos['es']:.1f} en={puntos['en']:.1f}")
    return idioma, razones


# --------------------------------------------------------------- ángulos -----

# La primera línea de cada correo, elegida por área porque lo que impresiona a
# un CISO no es lo mismo que lo que impresiona a un laboratorio de IA.
#
# TODO LO DE AQUÍ ES UNA PLANTILLA EJEMPLO. Sustituye cada apertura por UN
# trabajo tuyo, concreto y con un resultado medible; y cada asunto por esa misma
# idea en cinco o seis palabras. Lo que pongas aquí se envía en tu nombre: no
# escribas nada que no puedas sostener en una entrevista.
#
# Si prefieres no tocar este archivo, escribe tus logros en `perfil.LOGROS` y
# cópialos aquí: es la misma fuente de verdad que usa el resto del sistema.
ANGULOS = {
    "ciber-ia": {
        "es": (
            "EJEMPLO — describe aquí, en dos o tres frases, UN trabajo tuyo de "
            "seguridad de IA y cómo mediste que funcionaba. Sustituye este texto "
            "por el tuyo (ver perfil.LOGROS['ia'])."
        ),
        "en": (
            "EXAMPLE — describe here, in two or three sentences, ONE AI-security "
            "project of your own and how you measured that it worked. Replace "
            "this text with yours (see perfil.LOGROS['ia'])."
        ),
        "asunto_es": "EJEMPLO — tu logro de seguridad de IA, en pocas palabras",
        "asunto_en": "EXAMPLE — your AI-security achievement, in a few words",
    },
    "ciberseguridad": {
        "es": (
            "EJEMPLO — describe aquí, en dos o tres frases, UN trabajo tuyo de "
            "ciberseguridad con su resultado concreto. Sustituye este texto por "
            "el tuyo (ver perfil.LOGROS['ciberseguridad'])."
        ),
        "en": (
            "EXAMPLE — describe here, in two or three sentences, ONE "
            "cybersecurity project of your own and its concrete outcome. Replace "
            "this text with yours (see perfil.LOGROS['ciberseguridad'])."
        ),
        "asunto_es": "EJEMPLO — tu logro de ciberseguridad, en pocas palabras",
        "asunto_en": "EXAMPLE — your cybersecurity achievement, in a few words",
    },
    "ia": {
        "es": (
            "EJEMPLO — describe aquí, en dos o tres frases, UN proyecto tuyo de "
            "IA o de datos y contra qué métrica lo evaluaste. Sustituye este "
            "texto por el tuyo (ver perfil.LOGROS['ia'])."
        ),
        "en": (
            "EXAMPLE — describe here, in two or three sentences, ONE AI or data "
            "project of your own and the metric you evaluated it against. "
            "Replace this text with yours (see perfil.LOGROS['ia'])."
        ),
        "asunto_es": "EJEMPLO — tu logro de IA, en pocas palabras",
        "asunto_en": "EXAMPLE — your AI project, in a few words",
    },
    "ti-general": {
        "es": (
            "EJEMPLO — describe aquí, en dos o tres frases, UNA tarea de TI o de "
            "automatización que hicieras y qué dejó resuelto. Sustituye este "
            "texto por el tuyo (ver perfil.LOGROS['ti'])."
        ),
        "en": (
            "EXAMPLE — describe here, in two or three sentences, ONE IT or "
            "automation task you did and what it solved. Replace this text with "
            "yours (see perfil.LOGROS['ti'])."
        ),
        "asunto_es": "EJEMPLO — tu logro de TI, en pocas palabras",
        "asunto_en": "EXAMPLE — your IT achievement, in a few words",
    },
}

# Cómo te presentas en el asunto, según el nivel del puesto. Las de "otro"
# describen QUÉ ERES: ajústalas a tu situación (estudiante, recién egresado,
# perfil junior…) para que el asunto no diga algo que no eres.
QUIEN_SOY = {
    "practicas": {
        "ciber-ia": ("Prácticas en seguridad de IA", "AI security internship"),
        "ciberseguridad": ("Prácticas en ciberseguridad", "Security internship"),
        "ia": ("Prácticas en IA", "AI internship"),
        "ti-general": ("Prácticas en TI", "IT internship"),
    },
    "otro": {
        "ciber-ia": ("Perfil de seguridad de IA", "AI security profile"),
        "ciberseguridad": ("Perfil de ciberseguridad", "Cybersecurity profile"),
        "ia": ("Perfil de IA", "AI profile"),
        "ti-general": ("Perfil de TI", "IT profile"),
    },
}


# ----------------------------------------------------------- habilidades -----

# Cada concepto agrupa los sinónimos que el clasificador puede haber marcado
# ("iso 27001", "isms", "sgsi" son lo mismo) y trae la frase con la que se
# escribe en el correo. `hecho` decide si la frase se escribe como "lo hice" o
# con su matiz de "lo estoy estudiando". VIENE EN False EN TODAS LAS ENTRADAS
# a proposito: esta copia no sabe que has hecho tu, y afirmar de mas en un
# correo es el error que no se puede deshacer. Pon True solo en aquello que
# puedas respaldar con un entregable tuyo, y describelo en perfil.LOGROS. `solo_ia` evita que un término del vocabulario de IA se
# cuele en un correo de GRC solo porque la palabra apareció en la descripción.
CONCEPTOS = [
    # --- GRC -------------------------------------------------------------------
    {"id": "sgsi", "claves": ["iso 27001", "iso/iec 27001", "isms", "sgsi"], "hecho": False,
     "es": "la gestión de un SGSI ISO/IEC 27001",
     "en": "ISO/IEC 27001 ISMS work"},
    {"id": "auditoria", "claves": ["internal audit", "auditoria interna", "gap analysis"], "hecho": False,
     "es": "auditoría interna",
     "en": "internal audit"},
    {"id": "anexo", "claves": ["annex a", "anexo a"], "hecho": False,
     "es": "el mapeo de hallazgos al Anexo A",
     "en": "mapping findings to Annex A"},
    {"id": "nist", "claves": ["nist csf", "nist", "800-61"], "hecho": False,
     "es": "el uso de NIST (CSF y 800-61) como marco de referencia",
     "en": "using NIST (CSF and 800-61) as the reference framework"},
    {"id": "riesgos", "claves": ["risk management", "gestion de riesgos", "risk assessment"], "hecho": False,
     "es": "matriz de riesgos",
     "en": "risk registers"},
    {"id": "politicas", "claves": ["security policies", "politicas de seguridad"], "hecho": False,
     "es": "redacción de políticas de seguridad",
     "en": "security policy writing"},
    {"id": "grc", "claves": ["grc", "governance", "compliance", "cumplimiento"], "hecho": False,
     "es": "trabajo de GRC",
     "en": "GRC work"},
    {"id": "sod", "claves": ["segregation of duties", "least privilege", "minimo privilegio"], "hecho": False,
     "es": "segregación de funciones y mínimo privilegio",
     "en": "segregation of duties and least privilege"},
    {"id": "marcos_ext", "claves": ["soc 2", "pci dss"], "hecho": False,
     "es": "SOC 2 y PCI DSS", "en": "SOC 2 and PCI DSS"},
    # --- Blue Team ----------------------------------------------------------
    {"id": "ir", "claves": ["incident response", "respuesta a incidentes", "runbook"], "hecho": False,
     "es": "respuesta a incidentes y runbooks",
     "en": "incident response and runbooks"},
    {"id": "triage", "claves": ["triage", "blue team", "soc analyst", "soc"], "hecho": False,
     "es": "triage en Windows y detección de persistencia",
     "en": "Windows triage and persistence detection"},
    {"id": "ransomware", "claves": ["ransomware"], "hecho": False,
     "es": "contención de ransomware",
     "en": "ransomware containment"},
    {"id": "phishing", "claves": ["phishing", "bec", "security awareness"], "hecho": False,
     "es": "políticas anti-BEC y concientización",
     "en": "anti-BEC policies and security awareness"},
    {"id": "hardening", "claves": ["windows hardening", "hardening", "endpoint security"], "hecho": False,
     "es": "hardening de endpoints Windows",
     "en": "Windows endpoint hardening"},
    {"id": "siem", "claves": ["siem", "microsoft sentinel", "sentinel", "microsoft defender",
                              "defender", "edr", "sc-200", "detection engineering",
                              "ingenieria de deteccion", "threat detection",
                              "deteccion de amenazas"], "hecho": False,
     "es": "SIEM y detección en Microsoft Sentinel y Defender, a nivel de estudio",
     "en": "SIEM and detection on Microsoft Sentinel and Defender, at study level"},
    # --- Identidad y accesos -------------------------------------------------
    {"id": "pam", "claves": ["pam", "privileged access", "active directory", "iam", "identity", "mfa"], "hecho": False,
     "es": "gestión de accesos privilegiados en Active Directory",
     "en": "privileged access management in Active Directory"},
    # --- Automatización ------------------------------------------------------
    {"id": "powershell", "claves": ["powershell", "batch", "scripting"], "hecho": False,
     "es": "automatización en PowerShell",
     "en": "PowerShell automation"},
    {"id": "python", "claves": ["python"], "hecho": False,
     "es": "Python aplicado a seguridad",
     "en": "Python applied to security work"},
    {"id": "automatizacion", "claves": ["automation", "automatizacion"], "hecho": False,
     "es": "automatizar tareas repetitivas de operación",
     "en": "automating repetitive operational work"},
    {"id": "nube", "claves": ["azure", "microsoft 365", "entra id", "linux", "bash"], "hecho": False,
     "es": "Azure, Microsoft 365 y Linux", "en": "Azure, Microsoft 365 and Linux"},
    # --- Seguridad de IA -----------------------------------------------------
    {"id": "redteam_llm", "claves": ["prompt injection", "inyeccion de prompts", "jailbreak",
                                     "guardrails", "red teaming", "red team", "adversarial",
                                     "llm security", "ai security", "ai safety"], "hecho": False,
     "es": "seguridad de LLM y evaluación de guardrails",
     "en": "LLM security and guardrail evaluation"},
    {"id": "evals", "claves": ["evals", "model evaluation"], "hecho": False,
     "es": "evaluación de modelos con métricas, no con impresiones",
     "en": "model evaluation against metrics rather than impressions"},
    {"id": "llm", "claves": ["llm", "large language model", "prompt engineering"], "hecho": False,
     "es": "trabajo práctico con LLM y diseño de prompts",
     "en": "hands-on work with LLMs and prompt design"},
    {"id": "ai_gov", "claves": ["ai governance", "nist ai rmf", "iso 42001", "eu ai act",
                                "responsible ai", "ai risk", "ai policy"], "hecho": False,
     "es": "gobernanza de IA (NIST AI RMF, ISO 42001), a nivel de estudio",
     "en": "AI governance (NIST AI RMF, ISO 42001), at study level"},
    {"id": "alineacion", "claves": ["alignment", "rlhf", "trust and safety",
                                    "content moderation", "data annotation"],
     "hecho": False, "solo_ia": True,
     "es": "alineación y trust & safety", "en": "alignment and trust & safety"},
]

_POR_CLAVE: dict[str, dict] = {}
for _c in CONCEPTOS:
    for _k in _c["claves"]:
        _POR_CLAVE.setdefault(_k, _c)

# Lo que cada apertura ya dijo. Repetirlo en el cuerpo suena a relleno.
YA_DICHO = {
    "ciber-ia": {"redteam_llm", "evals", "llm", "python"},
    "ciberseguridad": {"sgsi", "auditoria", "anexo", "riesgos"},
    "ia": {"evals", "llm", "python", "redteam_llm"},
    "ti-general": {"powershell", "pam", "hardening", "automatizacion"},
}


# De qué área de `perfil.LOGROS` sale el hecho de cada concepto. Existe para que
# el correo hable del CV de QUIEN USA esta copia y no de una frase escrita aquí.
_AREA_DE_CONCEPTO = {
    "sgsi": "ciberseguridad", "auditoria": "ciberseguridad", "anexo": "ciberseguridad",
    "nist": "ciberseguridad", "riesgos": "ciberseguridad", "politicas": "ciberseguridad",
    "grc": "ciberseguridad", "sod": "ciberseguridad", "marcos_ext": "ciberseguridad",
    "ir": "ciberseguridad", "triage": "ciberseguridad", "ransomware": "ciberseguridad",
    "phishing": "ciberseguridad", "hardening": "ciberseguridad", "siem": "ciberseguridad",
    "pam": "ciberseguridad",
    "redteam_llm": "ia", "evals": "ia", "llm": "ia", "ai_gov": "ia", "alineacion": "ia",
    "powershell": "ti", "python": "ti", "automatizacion": "ti", "nube": "ti",
}


def _logro_para(concepto: dict, idioma: str, usados: set[str]) -> str | None:
    """El logro declarado que habla DE ESTE concepto, o None si no hay ninguno.

    Dos condiciones, y las dos hacen falta:

      - **Idioma.** En español se miran `perfil.LOGROS`; en inglés, `LOGROS_EN`.
        Citar un logro escrito en español dentro de un correo en inglés se nota
        más que quedarse corto, así que si no hay versión en inglés no hay
        hecho: el concepto se cuenta como estudio.
      - **Tema.** El texto del logro tiene que mencionar alguna de las `claves`
        del concepto. Elegir solo por área bastaría para citar un logro de
        phishing bajo el concepto de SGSI, dentro de una frase que presume de
        cubrir justo lo que la vacante pide. Eso es exactamente la clase de
        afirmación descolocada que este módulo existe para no cometer.

    Los que siguen siendo la plantilla ("EJEMPLO — …") no cuentan: mientras
    nadie rellene su perfil, el correo no tiene ningún hecho que afirmar.
    """
    fuente = LOGROS if idioma == "es" else LOGROS_EN
    candidatos = []
    for logro in (fuente.get(_AREA_DE_CONCEPTO.get(concepto["id"], "")) or []):
        texto = (logro or "").strip()
        if not texto or texto in usados:
            continue
        if texto.upper().startswith(("EJEMPLO", "EXAMPLE")):
            continue
        candidatos.append(texto)
    if not candidatos:
        return None

    # Se compara con `nucleo.tiene_termino`, que respeta límites de palabra, y
    # NO por subcadena. Con subcadena las claves cortas casan dentro de
    # cualquier palabra: 'soc' dentro de "encuesta social" y 'pam' dentro de
    # "campamento" bastaban para citar un logro que no tiene nada que ver, en
    # una frase que presume de cubrir justo lo que la vacante pide. Es el mismo
    # fallo que `tiene_termino` existe para evitar ('intern' en "internal").
    marcas = [normalizar(c) for c in concepto.get("claves", [])]
    marcas.append(normalizar(concepto["id"]).replace("_", " "))
    for texto in candidatos:
        plano = normalizar(texto)
        if any(m and tiene_termino(plano, m) for m in marcas):
            return texto
    return None


def _conceptos_coincidentes(habilidades: list[str], area: str,
                            idioma: str = "es") -> tuple[list[dict], list[dict]]:
    """Separa lo demostrado de lo que solo está en estudio, sin repetir apertura.

    Lo que se escribe sale del perfil de quien usa la copia, nunca de una frase
    escrita aquí:

      - si declaró un logro de ESE tema y EN ESE idioma, ese texto es el que
        viaja y cuenta como demostrado;
      - si no, se usa la frase neutra del catálogo, que nombra el área sin
        afirmar que se haya hecho nada, y el concepto va a estudio.

    Por eso la clasificación hecho/estudio depende del idioma: un mismo perfil
    puede tener con qué presumir en español y no tenerlo todavía en inglés.
    """
    vistos: set[str] = set()
    usados: set[str] = set()
    hechos: list[dict] = []
    estudio: list[dict] = []
    # Se ordena por el peso que perfil.py le da a la habilidad: lo más
    # diferenciador primero.
    ordenadas = sorted(habilidades, key=lambda h: -HABILIDADES.get(h, 0))
    for hab in ordenadas:
        concepto = _POR_CLAVE.get(hab)
        if concepto is None or concepto["id"] in vistos:
            continue
        if concepto["id"] in YA_DICHO.get(area, set()):
            continue
        if concepto.get("solo_ia") and area not in ("ia", "ciber-ia"):
            continue
        vistos.add(concepto["id"])
        propio = _logro_para(concepto, idioma, usados)
        if propio:
            usados.add(propio)
            hechos.append({**concepto, idioma: propio, "hecho": True})
        else:
            estudio.append(concepto)
    return hechos[:3], estudio[:2]


# --------------------------------------------------------------- asunto ------

# Siglas que tienen que seguir en mayúsculas cuando hay que rescatar un título
# escrito TODO EN MAYÚSCULAS. Sin esta lista, .capitalize() dejaba
# "ANALISTA DE CIBERSEGURIDAD JR" como "Analista de ciberseguridad jr" y
# "PRACTICANTE TI" como "Practicante ti".
_SIGLAS = {
    "ti", "it", "ia", "ai", "ml", "bi", "qa", "rh", "hr", "sap", "erp", "crm",
    "sgsi", "isms", "grc", "iso", "nist", "soc", "siem", "edr", "xdr", "dlp",
    "pam", "iam", "mfa", "sso", "ciso", "cio", "cto", "vpn", "api", "sql",
    "aws", "gcp", "sre", "noc", "iot", "pki", "dfir", "csirt", "devops",
    "devsecops", "jr", "sr", "ux", "ui", "etl", "llm", "nlp", "kpi", "poc",
    "cdmx", "usa", "us", "uk", "mx", "eeuu", "sox", "itgc", "pci", "dss",
}
# Partículas que van en minúscula dentro de un título, salvo al principio.
_ATONAS = {
    "de", "del", "la", "las", "el", "los", "y", "e", "en", "para", "por",
    "con", "a", "al", "o", "u", "the", "of", "and", "in", "for", "to", "at",
    "on", "an",
}
_RX_PALABRA = re.compile(r"^([^\w]*)(\w[\w'’·-]*)(.*)$", re.UNICODE)

# Etiquetas de género de las ofertas europeas y mexicanas: "(m/f/d)",
# "(all genders)", "(H/F)", "Becario (a)". No aportan nada a la frase.
_RX_GENERO = re.compile(
    r"\s*\(\s*(?:[mwfhdxsi](?:\s*[/|]\s*[mwfhdxsi])+|all\s+genders?|"
    r"todos\s+los\s+g[eé]neros|[ao](?:\s*/\s*[ao])?)\s*\)",
    re.I,
)
# Códigos internos entre corchetes: "[IC3]", "[AI Team]", "[Remote / Global]".
# Además de no decir nada, dejaban corchetes en el cuerpo y el correo parecía
# tener marcadores sin sustituir.
_RX_CORCHETES = re.compile(r"\s*\[[^\]]*\]")
# Cola de marketing pegada al título con un separador.
_RX_COLA = re.compile(
    r"\s*[|/–—]\s*[^|/–—]*\b(?:100\s*%|remot\w*|h[ií]brid\w*|presencial|"
    r"urgente|inmediat\w*|sueldo|salario|prestaciones|contrataci[oó]n|"
    r"only|full[-\s]?time|part[-\s]?time|medio\s+tiempo|temporal)\b[^|/–—]*$",
    re.I,
)


def _capitalizar_titulo(t: str) -> str:
    """Title Case que respeta siglas y partículas."""
    palabras = t.split(" ")
    salida: list[str] = []
    for i, p in enumerate(palabras):
        m = _RX_PALABRA.match(p)
        if not m:
            salida.append(p)
            continue
        pre, nucleo, post = m.groups()
        bajo = nucleo.lower()
        if bajo in _SIGLAS:
            nucleo = nucleo.upper()
        elif i > 0 and bajo in _ATONAS:
            nucleo = bajo
        else:
            nucleo = bajo[:1].upper() + bajo[1:]
        salida.append(pre + nucleo + post)
    return " ".join(salida)


def _grita(t: str) -> bool:
    letras = [c for c in t if c.isalpha()]
    return bool(letras) and sum(c.isupper() for c in letras) / len(letras) > 0.7


def _titulo_legible(titulo: str) -> str:
    """El título de la vacante tal y como puede escribirse dentro de una frase.

    El título crudo se metía sin tocar en "Le escribo por la vacante de ...",
    con tres consecuencias feas: los títulos en mayúsculas gritaban en mitad
    del párrafo, los códigos entre corchetes parecían marcadores sin sustituir
    y las colas de marketing ("- México Only", "| 100% Remoto") delataban que
    el texto venía copiado de un portal.
    """
    t = re.sub(r"\s+", " ", (titulo or "")).strip()
    t = _RX_CORCHETES.sub(" ", t)
    t = _RX_GENERO.sub(" ", t)
    t = _RX_COLA.sub("", t)
    t = re.sub(r"\s*[-–—]\s*[^-–—]*\b(?:only|remoto?|remote|h[ií]brido)\b\s*$", "", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip(" ,;:-–—|/")
    if _grita(t):
        t = _capitalizar_titulo(t)
    return t or re.sub(r"\s+", " ", (titulo or "")).strip()


def _puesto_limpio(titulo: str) -> str:
    """El título recortado a lo que cabe en un asunto sin ruido de marketing."""
    t = _titulo_legible(titulo)
    t = re.split(r"\s+[-–—|(]\s*|\s*\(", t)[0].strip(" -–—|")
    if _grita(t):
        t = _capitalizar_titulo(t)
    return t[:52].strip() or _titulo_legible(titulo)[:52]


def _empresa_limpia(empresa: str) -> str:
    """Quita la puntuacion final del nombre.

    Hay empresas registradas como "DaCodes." con punto incluido, y al meterlas
    a mitad de una frase salia "en DaCodes..". Se recorta solo el final; los
    puntos internos de siglas como "S.A." se respetan.
    """
    e = re.sub(r"\s+", " ", (empresa or "").strip())
    return e.rstrip(" .,;:·-–—") or e


def _asunto(v: dict, area: str, idioma: str, nivel: str) -> str:
    quien = QUIEN_SOY["practicas" if nivel == "practicas" else "otro"][area]
    quien = quien[0] if idioma == "es" else quien[1]
    hecho = ANGULOS[area][f"asunto_{idioma}"]
    puesto = _puesto_limpio(_campo(v, "titulo"))
    union = "para" if idioma == "es" else "for"

    # Si el titulo del puesto ya dice que son practicas, anteponer "Practicas
    # para..." suena a tartamudeo: "Security internship for Security Engineer
    # Intern". En ese caso el titulo habla por si solo.
    if re.search(r"\b(intern|internship|becari|practicant|pr[aá]cticas|trainee)\b",
                 puesto, re.I):
        largo = f"{puesto}: {hecho}"
        return largo if len(largo) <= 92 else f"{puesto}"[:92]

    largo = f"{quien} {union} {puesto}: {hecho}"
    if len(largo) <= 92:
        return largo
    corto = f"{quien} {union} {puesto}"
    return corto if len(corto) <= 92 else f"{quien}: {hecho}"[:92]


# ---------------------------------------------------------------- cuerpo -----

def _parrafo_vacante(v: dict, idioma: str, hechos: list[dict], estudio: list[dict]) -> list[str]:
    titulo = re.sub(r"\s+", " ", _campo(v, "titulo")).strip()
    empresa = _empresa_limpia(_campo(v, "empresa"))
    parrafos: list[str] = []

    if idioma == "es":
        destino = f" en {empresa}" if empresa else ""
        cabeza = f"Le escribo por la vacante de {titulo}{destino}."
        if hechos:
            lista = _lista_es([c["es"] for c in hechos])
            cuantas = "Tres" if len(hechos) == 3 else ("Dos" if len(hechos) == 2 else "Una")
            cosa = "cosas que piden" if len(hechos) > 1 else "cosa que piden"
            cabeza += f" {cuantas} {cosa} y que ya hice: {lista}."
        else:
            cabeza += (
                " Mi perfil es GRC más Blue Team: documentación de seguridad,"
                " respuesta a incidentes y automatización en PowerShell."
                " Lo que respalde cada afirmación sale de tu perfil."
            )
        parrafos.append(cabeza)
        if estudio:
            parrafos.append(
                f"También toco {_lista_es([c['es'] for c in estudio])}, y prefiero"
                " decirlo como es: ahí voy a nivel de laboratorio y estudio, no de"
                " producción."
            )
        parrafos.append(
            "Estudio la Licenciatura en Seguridad en Tecnologías de la Información"
            " y adjunto mi CV."
        )
    else:
        destino = f" at {empresa}" if empresa else ""
        cabeza = f"I'm writing about the {titulo} role{destino}."
        if hechos:
            lista = _lista_en([c["en"] for c in hechos])
            cabeza += f" Things the role asks for that I have already done: {lista}."
        else:
            cabeza += (
                " My profile is GRC plus Blue Team: security documentation,"
                " incident response and PowerShell automation, all of it from a"
                " real internship with deliverables, not from courses."
            )
        parrafos.append(cabeza)
        if estudio:
            parrafos.append(
                f"I also work with {_lista_en([c['en'] for c in estudio])}, and I'd"
                " rather be precise about it: that part is lab and study level, not"
                " production."
            )
        parrafos.append(
            f"I'm {CANDIDATO['grado']}, based in {CANDIDATO['ciudad']}."
            f" I work in English at a {CANDIDATO['ingles']} level."
            " My CV is attached."
        )
    return parrafos


def _lista(items: list[str], conjuncion: str) -> str:
    """Une frases largas sin que se pierda dónde acaba una y empieza la otra.

    Los elementos no son palabras sueltas, son frases que ya llevan comas y
    conjunciones dentro ("políticas anti-BEC con validación fuera de banda y
    concientización"). Unirlas con comas producía cosas como "...y
    concientización y trabajo de GRC con entregables, no solo teoría y
    hardening de endpoints", donde no se sabe qué "y" separa qué: 167 correos
    salían así. Cuando algún elemento ya trae coma o conjunción, se separa con
    punto y coma, que es exactamente para lo que sirve.
    """
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    complejos = any("," in i or f" {conjuncion} " in i for i in items)
    sep = "; " if complejos else ", "
    return sep.join(items[:-1]) + f"{';' if complejos else ''} {conjuncion} " + items[-1]


def _lista_es(items: list[str]) -> str:
    return _lista(items, "y")


def _lista_en(items: list[str]) -> str:
    return _lista(items, "and")


def _parrafo_ubicacion(v: dict, idioma: str) -> str:
    """Nunca ofrece mudanza: si la vacante la exige, se deja a decisión de él."""
    if bool(_campo(v, "requiere_mudanza", 0)):
        if idioma == "es":
            return (
                "Estoy en Monterrey. Si el puesto admite esquema remoto o híbrido,"
                " me encantaría platicarlo."
            )
        return (
            "I'm based in Monterrey, Mexico. If the role can be done remotely or"
            " in a hybrid setup, I'd be glad to talk about it."
        )
    if _en_monterrey(v) and not _es_remota(v):
        if idioma == "es":
            return (
                "Vivo en Monterrey, así que puedo presentarme presencial desde el"
                " primer día, sin mudanza de por medio."
            )
        return (
            "I live in Monterrey, so I can be on site from day one, with no"
            " relocation involved."
        )
    if _es_remota(v):
        if idioma == "es":
            return (
                "Trabajo desde Monterrey (UTC-6), que se solapa con el horario de"
                " oficina de Estados Unidos."
            )
        return (
            "I work from Monterrey, Mexico (UTC-6), which fully overlaps US"
            " business hours."
        )
    if idioma == "es":
        return "Estoy en Monterrey (UTC-6) y puedo coordinarme con su horario."
    return "I'm based in Monterrey, Mexico (UTC-6) and can align with your hours."


def _pedido(idioma: str) -> str:
    if idioma == "es":
        return "¿Tendría 15 minutos esta semana o la próxima para una llamada?"
    return "Would you have 15 minutes for a call this week or next?"


def _firma(idioma: str) -> str:
    """Firma de cuatro líneas, cada una dentro de ANCHO.

    Los dos enlaces iban antes en la misma línea separados por '·': 84
    caracteres, seis por encima del ancho del cuerpo. En un cliente de correo
    que no reflowea, esa línea se partía por la mitad y dejaba media URL
    colgando, que además rompe el enlace al hacer clic. Uno por línea.
    """
    c = CANDIDATO
    lineas = [
        "Gracias por el tiempo," if idioma == "es" else "Best,",
        c["nombre"],
        f"{c['telefono']} · {c['correo']}",
        c["github"],
        c["linkedin"],
    ]
    return "\n".join(lineas)


# ---------------------------------------------------------------- avisos -----

def _saludo(v: dict, idioma: str, contacto: dict | None) -> str:
    """El saludo se resuelve solo. Nunca deja trabajo manual.

    Antes ponia "Hola [Nombre]:" y un aviso pidiendo sustituirlo. Eso convertia
    cada correo en una tarea de cinco minutos, y un sistema que deja tarea es un
    sistema que no se usa: el objetivo es que el usuario solo revise y envie.

    Con contacto conocido va el nombre de PILA (el completo es la firma del
    correo en masa, y ademas obliga a adivinar el genero por el apellido).
    Sin contacto NO se inventa a nadie: se saluda al equipo de la empresa, que
    es correcto, enviable tal cual y no finge una cercania que no existe.
    """
    pila = ((contacto or {}).get("nombre") or "").strip().split(" ")[0]
    if pila:
        return f"Estimado/a {pila}:" if idioma == "es" else f"Hi {pila},"

    empresa = _empresa_limpia(str(_campo(v, "nombre_limpio") or _campo(v, "empresa")))
    if idioma == "es":
        return f"Hola, equipo de {empresa}:" if empresa else "Hola, buen dia:"
    return f"Hello {empresa} team," if empresa else "Hello,"


def _dias_desde(fecha: str) -> int | None:
    if not fecha:
        return None
    try:
        d = datetime.fromisoformat(str(fecha)[:10]).date()
    except ValueError:
        return None
    return (date.today() - d).days


def _avisos(v: dict, area: str, idioma: str, idioma_detectado: str,
            hechos: list[dict], estudio: list[dict],
            contacto: dict | None = None) -> tuple[list[str], list[str]]:
    """Advertencias honestas para el usuario ANTES de enviar. Siempre en español."""
    avisos: list[str] = []
    codigos: list[str] = []

    def añadir(codigo: str, texto: str) -> None:
        codigos.append(codigo)
        avisos.append(texto)

    # El aviso ya no manda hacer nada: solo dice a quien va. Pedir "sustituye
    # [Nombre]" convertia cada correo en tarea manual, que es justo lo que este
    # sistema existe para quitar.
    if not contacto:
        añadir("contacto",
               "Va dirigido al equipo: no hay contacto verificado en esta empresa. "
               "Es enviable así; si aparece la persona, el saludo se pone solo.")

    anios = _campo(v, "anios_exigidos", None)
    if isinstance(anios, int) and anios >= 3:
        evidencia = str(_campo(v, "evidencia_experiencia")).strip()
        extra = f' La vacante dice: "{evidencia[:120]}".' if evidencia else ""
        añadir("experiencia",
               f"Pide {anios} años de experiencia y tú no los tienes: vas con "
               f"desventaja explícita, no por perfil sino por filtro.{extra}")

    if bool(_campo(v, "requiere_mudanza", 0)):
        añadir("mudanza",
               f"Es presencial en {_campo(v, 'ubicacion') or 'otra ciudad'}: "
               "implicaría mudarte. El correo NO ofrece mudanza; si estás dispuesto, "
               "dilo tú a mano antes de enviarlo.")

    titulo_n = _normalizar(_campo(v, "titulo"))
    senior = [t for t in NIVEL_EXCLUIR if re.search(rf"\b{re.escape(t)}\b", titulo_n)]
    if senior or str(_campo(v, "nivel")) == "excluido":
        etiqueta = senior[0] if senior else "nivel excluido"
        añadir("senior",
               f"El título es de nivel superior ('{etiqueta}'): no es un puesto de "
               "entrada y probablemente te filtren antes de leerte.")

    comercial = [t for t in ROL_NO_TECNICO if t in titulo_n]
    if comercial:
        añadir("no-tecnico",
               f"Parece un puesto comercial o no técnico ('{comercial[0]}'), no de "
               "ingeniería. Revisa si de verdad quieres esto.")

    ver = v.get("verificacion") or {}
    estado = ver.get("estado") if ver else _campo(v, "ver_estado")
    if estado and estado != "viva":
        añadir("sin-verificar",
               f"No se pudo confirmar que siga abierta (estado: {estado}). "
               "Ábrela antes de escribir.")

    dias = _dias_desde(_campo(v, "publicado"))
    if dias is not None and dias > 30:
        añadir("antigua",
               f"Se publicó hace {dias} días. A esa edad muchas ya están cubiertas "
               "aunque el enlace siga vivo.")

    if not bool(_campo(v, "elegible_mx", 1)):
        geo = next((m for m in _motivos_de(v)
                    if "restring" in m.lower() or "zona gris" in m.lower()
                    or "exige" in m.lower() or "visa" in m.lower()), "")
        añadir("geo",
               "El análisis marcó que quizá no puedas aplicar desde México"
               + (f": {geo[:160]}" if geo else "."))

    ubic_n = _normalizar(_campo(v, "ubicacion"))
    if _RX_EXTRANJERA.search(ubic_n) and not _es_remota(v):
        añadir("visa",
               "Es presencial en el extranjero: requeriría visa y patrocinio, "
               "que hoy no tienes.")

    if not hechos and not estudio:
        añadir("sin-habilidades",
               "La vacante no coincidió con ninguna habilidad de tu CV, así que el "
               "correo va con tu perfil genérico. Lee la vacante entera antes de "
               "mandarlo: puede que no aplique.")

    if any(c["id"] == "siem" for c in estudio):
        añadir("sc200",
               "El correo menciona la SC-200 como examen agendado y no presentado. "
               "No la presentes como obtenida en ningún otro lado.")

    veredicto = str(_campo(v, "veredicto"))
    if veredicto in ("zona-gris", "explorar"):
        añadir("veredicto",
               f"El sistema la clasificó como '{veredicto}', no como 'aplicar-ya': "
               "es una apuesta, no un tiro seguro.")

    if idioma != idioma_detectado:
        añadir("idioma-forzado",
               f"Forzaste el idioma '{idioma}' pero la vacante parece estar en "
               f"'{idioma_detectado}'.")

    return avisos, codigos


# ------------------------------------------------------------------- API -----

def generar(vacante: dict, idioma: str = "auto", contacto: dict | None = None) -> dict:
    """Devuelve {'asunto', 'cuerpo', 'angulo', 'avisos'}.

    Acepta tanto la fila cruda de SQLite como el diccionario que devuelve
    `almacen.consultar()`. Además de las cuatro claves del contrato incluye
    'idioma', 'habilidades_usadas' y 'codigos_aviso', que es lo que necesitan
    el panel y las pruebas para comprobar el resultado sin re-parsear el texto.
    """
    if not isinstance(vacante, dict):
        raise TypeError("generar() espera un diccionario de vacante")

    detectado, _razones = detectar_idioma(vacante)
    idioma = detectado if idioma == "auto" else idioma
    if idioma not in ("es", "en"):
        raise ValueError(f"idioma no soportado: {idioma!r} (usa 'auto', 'es' o 'en')")

    area = _area_de(vacante)
    nivel = str(_campo(vacante, "nivel"))
    habilidades = _habilidades_de(vacante)
    hechos, estudio = _conceptos_coincidentes(habilidades, area, idioma)

    saludo = _saludo(vacante, idioma, contacto)
    parrafos = [ANGULOS[area][idioma]]
    parrafos += _parrafo_vacante(vacante, idioma, hechos, estudio)
    parrafos.append(_parrafo_ubicacion(vacante, idioma))
    parrafos.append(_pedido(idioma))

    cuerpo = saludo + "\n\n" + "\n\n".join(_envolver(p) for p in parrafos)
    cuerpo += "\n\n" + _firma(idioma)

    avisos, codigos = _avisos(vacante, area, idioma, detectado, hechos, estudio, contacto)

    return {
        "asunto": _asunto(vacante, area, idioma, nivel),
        "cuerpo": cuerpo,
        "angulo": area,
        "avisos": avisos,
        "idioma": idioma,
        "habilidades_usadas": [c["id"] for c in hechos + estudio],
        "codigos_aviso": codigos,
    }


def generar_por_id(vacante_id: str, idioma: str = "auto") -> dict:
    """Igual que `generar`, pero leyendo la vacante de la base por su id."""
    with conexion() as con:
        fila = con.execute(
            "SELECT * FROM vacantes WHERE id = ?", (vacante_id,)
        ).fetchone()
    if fila is None:
        raise KeyError(f"no existe la vacante {vacante_id!r} en la base")
    vacante = dict(fila)
    correo = generar(vacante, idioma=idioma)
    correo["id"] = vacante["id"]
    correo["titulo"] = vacante["titulo"]
    correo["empresa"] = vacante["empresa"]
    correo["url"] = vacante["url"]
    return correo


def generar_lote(veredicto: str = "aplicar-ya", limite: int = 20) -> list[dict]:
    """Correos para las mejores vacantes vivas de un veredicto, de mayor score a menor."""
    vacantes = consultar(veredictos=[veredicto], minimo=0.0, solo_vivas=True, limite=limite)
    lote: list[dict] = []
    for v in vacantes:
        correo = generar(v)
        correo["id"] = v.get("id")
        correo["titulo"] = v.get("titulo")
        correo["empresa"] = v.get("empresa")
        correo["url"] = v.get("url")
        correo["score"] = v.get("score")
        lote.append(correo)
    return lote


def formatear(correo: dict) -> str:
    """Un correo listo para leer en consola, con sus avisos debajo."""
    cabecera = f"{correo.get('empresa', '')} — {correo.get('titulo', '')}".strip(" —")
    partes = [
        "=" * ANCHO,
        cabecera,
        f"[{correo['angulo']} · {correo['idioma']}] {correo.get('url', '')}",
        "=" * ANCHO,
        f"Asunto: {correo['asunto']}",
        "",
        correo["cuerpo"],
        "",
        "-- avisos antes de enviar " + "-" * (ANCHO - 26),
    ]
    partes += [f"  - {a}" for a in correo["avisos"]]
    return "\n".join(partes)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    for correo in generar_lote(limite=2):
        print(formatear(correo))
        print()

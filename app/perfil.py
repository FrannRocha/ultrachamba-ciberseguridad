"""
Perfil del candidato: única fuente de verdad sobre la persona que busca empleo.

Este archivo es una PLANTILLA DE EJEMPLO. Sustituye los valores de identidad
(CANDIDATO, POSTULACION, LOGROS, CERTIFICACIONES, COMPETENCIAS) por los tuyos;
son marcadores, no describen a nadie real. El vocabulario del clasificador
(HABILIDADES, AREA_*, NIVEL_*, geografía) NO es personal: es el motor de
scoring de ciberseguridad e IA, consérvalo salvo que quieras ajustar el
criterio. Al editar tu identidad aquí, todo el sistema se actualiza solo.
"""

CANDIDATO = {
    # EJEMPLO — reemplaza por tus datos reales. Estos valores son marcadores.
    "nombre": "EJEMPLO — Tu Nombre Apellido",
    "correo": "tu-correo@example.com",
    "telefono": "+00 000 000 0000",
    "linkedin": "https://www.linkedin.com/in/tu-usuario",
    "github": "https://github.com/tu-usuario",
    # Ciudad/zona por defecto = mercado de Monterrey (no es dato personal, es el
    # mercado que cubren las fuentes por defecto). Cámbialo a tu ciudad.
    "ciudad": "Monterrey, Nuevo Leon, Mexico",
    "zona_horaria": "America/Monterrey (UTC-6)",
    "titulo_objetivo": "Practicas / Internship en Ciberseguridad (GRC, Blue Team, SOC) o IA (AI Safety, Red Teaming de LLM)",
    "grado": "EJEMPLO — Tu carrera y universidad (años)",
    "ingles": "B2 / intermedio",
    "espanol": "nativo",
    "requiere_patrocinio_visa": True,
    "puede_presencial": ["Monterrey", "Nuevo Leon", "Area Metropolitana de Monterrey"],
    "acepta_remoto_global": True,
}

# Municipios del Area Metropolitana de Monterrey: cualquiera cuenta como
# "presencial viable" sin mudanza.
AMM = [
    "monterrey", "nuevo leon", "san pedro garza garcia", "san nicolas",
    "guadalupe", "apodaca", "santa catarina", "escobedo", "garcia",
    "juarez, n", "santiago, n", "cadereyta", "salinas victoria", "mty",
]

# Habilidades verificables del CV, con el peso que cada una aporta al fit.
# El peso refleja qué tan diferenciadora es esa habilidad para él.
HABILIDADES = {
    # GRC — su núcleo más fuerte y documentado
    "iso 27001": 10, "iso/iec 27001": 10, "isms": 9, "sgsi": 9,
    "nist csf": 8, "nist": 6, "800-61": 8, "annex a": 7, "anexo a": 7,
    "risk management": 7, "gestion de riesgos": 7, "risk assessment": 7,
    "internal audit": 8, "auditoria interna": 8, "gap analysis": 7,
    "compliance": 6, "cumplimiento": 6, "security policies": 7,
    "politicas de seguridad": 7, "governance": 6, "grc": 10,
    "soc 2": 5, "pci dss": 4, "remediation plan": 6,
    # Como se escribe GRC en los anuncios mexicanos. Faltaban todos, y el
    # efecto era grave y silencioso: una vacante de Control Interno de TI
    # --matriz de riesgos, CSF, apoyo a auditoria-- puntuaba CERO en
    # habilidades coincidentes, porque el diccionario solo hablaba ingles de
    # consultora.
    "control interno": 8, "matriz de riesgos": 9, "riesgos y controles": 9,
    "analisis de riesgos": 8, "cyber strategic framework": 8,
    "cumplimiento normativo": 6, "coso": 5, "sox": 4,
    "efectividad operativa": 6, "control documental": 5,
    "auditoria externa": 6, "auditoria de ti": 8, "auditoria interna de ti": 9,
    # Vocabulario de ROL, no de herramienta. Los anuncios de becario rara vez
    # nombran una tecnologia: dicen "apoyo a la seguridad de la informacion" y
    # ya. Un anuncio de IT Security Intern puntuaba CERO con el diccionario
    # tecnico, siendo un encaje evidente.
    "seguridad de la informacion": 7, "seguridad informatica": 7,
    "seguridad de ti": 7, "auditorias de seguridad": 7,
    "monitoreo de seguridad": 7, "gestion de vulnerabilidades": 7,
    "politicas y procedimientos": 5, "concientizacion": 5,
    # Blue Team / operaciones
    "incident response": 9, "respuesta a incidentes": 9, "runbook": 7,
    "blue team": 9, "soc analyst": 8, "soc": 6, "triage": 7,
    "siem": 8, "edr": 8, "microsoft sentinel": 9, "sentinel": 6,
    "microsoft defender": 9, "defender": 5, "sc-200": 9,
    "endpoint security": 7, "windows hardening": 8, "hardening": 6,
    "threat detection": 7, "deteccion de amenazas": 7,
    "ransomware": 7, "phishing": 7, "bec": 7, "security awareness": 7,
    "detection engineering": 7, "ingenieria de deteccion": 7,
    # Identidad y accesos
    "active directory": 8, "pam": 8, "privileged access": 8,
    "least privilege": 7, "minimo privilegio": 7, "iam": 6, "mfa": 5,
    "identity": 5, "segregation of duties": 6,
    # IA / seguridad de IA — su diferenciador raro
    "ai safety": 10, "ai security": 10, "llm security": 10,
    "prompt injection": 10, "inyeccion de prompts": 10,
    "red teaming": 9, "red team": 7, "adversarial": 8,
    "guardrails": 9, "jailbreak": 9, "model evaluation": 8,
    "evals": 8, "trust and safety": 8, "content moderation": 5,
    "llm": 7, "large language model": 7, "prompt engineering": 7,
    "data annotation": 4, "rlhf": 5, "alignment": 8,
    "responsible ai": 7, "ai governance": 9, "ai policy": 6,
    "ai risk": 8, "nist ai rmf": 9, "iso 42001": 9, "eu ai act": 7,
    # Automatización
    "powershell": 9, "python": 7, "batch": 4, "scripting": 5,
    "automation": 5, "automatizacion": 5, "linux": 4,
    "bash": 3, "azure": 5, "microsoft 365": 5, "entra id": 6,
}

# Señales de que la vacante es alcanzable para alguien sin años de experiencia.
NIVEL_PRACTICAS = [
    "intern", "internship", "interno de", "becario", "becaria", "beca ",
    "practicante", "practicas profesionales", "practicas ", "trainee",
    "co-op", "coop program", "apprentice", "aprendiz", "student program",
    "estudiante", "summer analyst", "working student", "werkstudent",
    "graduate program", "programa de graduados", "early talent",
    "residencia profesional", "servicio social",
]
NIVEL_JUNIOR = [
    "junior", "jr", "entry level", "entry-level", "nivel inicial",
    "associate", "asociado", "new grad", "recien egresado", "graduate",
    "early career", "level 1", "tier 1", "tier i", "l1",
    "principiante", "sin experiencia",
]
NIVEL_EXCLUIR = [
    "senior", "sr", "snr", "staff", "principal", "lead", "leader", "head of",
    "director", "vp", "vice president", "chief", "manager", "gerente",
    "architect", "arquitecto", "expert", "especialista senior",
    "distinguished", "fellow", "iii", "iv", "sme", "supervisor", "jefe",
    "coordinador", "coordinator",
]

# Dominios que usan las mismas palabras que la seguridad ("auditoria",
# "riesgo", "control interno") pero que NO son ciberseguridad. Si el título
# los nombra y no hay un término fuerte de seguridad, la vacante queda fuera.
NEGATIVO_DOMINIO = [
    "fiscal", "contable", "contabilidad", "impuestos", "actuari*",
    "nomina", "tesoreria", "cobranza", "credito", "crediticio",
    "seguros", "siniestros", "financiero", "financiera", "balances",
    "auditoria fiscal", "auditoria financiera", "calidad", "ambiental",
    "seguridad e higiene", "seguridad industrial", "seguridad patrimonial",
    "seguridad fisica", "guardia", "vigilancia",
]

# Roles no técnicos: siguen siendo visibles, pero no son el objetivo.
ROL_NO_TECNICO = [
    "comercial", "ventas", "sales", "account executive", "business development",
    "marketing", "reclutamiento", "recursos humanos", "atencion a clientes",
    "customer success", "preventa", "pre-sales",
]

# Palabras que definen el área.
# El sufijo '*' significa "coincide como prefijo": lo necesitan las palabras
# compuestas del español (ciberseguridad) y los plurales (riesgos, amenazas).
# Términos que POR SÍ SOLOS acreditan que la vacante es de ciberseguridad.
AREA_CIBER = [
    "security", "securit*", "cyber*", "ciber*", "infosec", "soc",
    "seguridad de la informacion", "seguridad informatica",
    "grc", "siem", "soar", "edr", "xdr", "dlp",
    "threat*", "amenaza*", "vulnerabilit*", "vulnerabilidad*",
    "pentest*", "penetration test*", "appsec", "malware", "ransomware",
    "phishing", "forensic*", "forense", "hardening", "ciso",
    "blue team", "red team", "purple team", "trust and safety",
    "iso 27001", "nist", "hacking", "ethical hack*", "owasp",
    "incident response", "respuesta a incidentes", "zero trust",
]

# Términos AMBIGUOS: existen igual en auditoría contable, riesgo financiero y
# cumplimiento legal. Solo cuentan como ciberseguridad si van acompañados de
# un término del contexto técnico de abajo.
# Sin esta separación, "Becario de Auditoria Fiscal" puntuaba 83/100.
AREA_CIBER_DEBIL = [
    "audit*", "auditor*", "risk*", "riesgo*", "compliance", "cumplimiento",
    "privacy", "privacidad", "fraud*", "identity", "iam", "control interno",
    "governance", "gobierno", "detection", "deteccion", "incident*",
]

# Contexto que convierte un término ambiguo en ciberseguridad de verdad.
CONTEXTO_TECNICO = [
    "ti", "it", "tecnologia*", "tecnologias", "sistemas", "informatica",
    "information technology", "cyber*", "ciber*", "security", "seguridad",
    "datos", "data", "digital", "software", "network", "redes", "red",
    "cloud", "nube", "infraestructura", "infrastructure", "sox", "itgc",
    "informacion", "aplicaciones", "applications", "devops", "sistemas de informacion",
]
AREA_IA = [
    # 'ai', 'ml' e 'ia' son seguros con límite de palabra: no casan dentro de
    # 'available' ni de 'tecnologia' porque ahí no hay frontera de palabra.
    "ai", "ml", "ia",
    "artificial intelligence", "inteligencia artificial",
    "machine learning", "aprendizaje automatico",
    "llm", "llms", "language model", "deep learning", "data scien*",
    "ciencia de datos", "nlp", "prompt*", "genai", "generative",
    "generativa", "annotation", "anotacion", "rlhf",
    "alignment", "alineacion", "evals", "neural", "chatbot",
    "computer vision", "vision artificial", "mlops",
]

# Señales de restricción geográfica que EXCLUYEN a alguien en México.
# Se buscan en la DESCRIPCIÓN, con límites de palabra.
BLOQUEO_GEO = [
    "us citizen", "u.s. citizen", "must be a us citizen",
    "security clearance", "ts/sci", "top secret", "public trust",
    "clearance required", "polygraph", "itar",
    "us only", "united states only", "usa only",
    "must reside in the united states", "must be located in the us",
    "must be based in the united states",
    "must live in the united states",
    "authorized to work in the united states",
    "eligible to work in the united states",
    "eu only", "europe only", "eea only", "uk only",
    "must be based in the uk", "right to work in the uk",
    "canada only", "must reside in canada",
    "india only", "australia only", "singapore only",
    "no visa sponsorship", "we do not sponsor", "unable to sponsor",
    "cannot provide sponsorship", "without sponsorship",
]

# Señales positivas de que alguien en México SÍ puede aplicar.
# Ojo: aquí NO van siglas cortas ambiguas como "mx", "est" o "cst":
# generaban falsos positivos al aparecer dentro de otras palabras.
APERTURA_GEO = [
    "worldwide", "anywhere", "work from anywhere", "any location",
    "any timezone", "fully distributed", "globally distributed",
    "latam", "latin america", "america latina", "latinoamerica",
    "mexico", "hire globally", "hiring globally", "anywhere in the world",
]

# --- Ubicación: patrones aplicados al CAMPO de ubicación (regex) ------------
# Este campo es la señal más fiable: "Remote - USA" es un remoto cerrado,
# aunque la descripción hable de un equipo global.

# Estados de EEUU: aparecen en ubicaciones como "Remote - Virginia, USA",
# que es un remoto cerrado aunque no diga "USA" pegado a "Remote".
ESTADOS_EEUU = (
    r"alabama|alaska|arizona|arkansas|california|colorado|connecticut|delaware"
    r"|florida|georgia|hawaii|idaho|illinois|indiana|iowa|kansas|kentucky"
    r"|louisiana|maine|maryland|massachusetts|michigan|minnesota|mississippi"
    r"|missouri|montana|nebraska|nevada|new\s+hampshire|new\s+jersey"
    r"|new\s+mexico|new\s+york|north\s+carolina|north\s+dakota|ohio|oklahoma"
    r"|oregon|pennsylvania|rhode\s+island|south\s+carolina|south\s+dakota"
    r"|tennessee|texas|utah|vermont|virginia|washington|wisconsin|wyoming"
)

PAISES_CERRADOS = (
    r"us\b|usa|u\.?s\.?a?\b|united\s+states|america\b|canada|uk\b"
    r"|united\s+kingdom|england|scotland|europe|emea|eea|eu\b|ireland"
    r"|germany|deutschland|france|spain|espana|portugal|poland|romania"
    r"|netherlands|belgium|switzerland|austria|sweden|norway|denmark|finland"
    r"|israel|india|pakistan|australia|new\s+zealand|anz\b|apac|japan|china"
    r"|korea|singapore|philippines|vietnam|indonesia|malaysia|thailand"
    r"|nigeria|kenya|egypt|south\s+africa|ghana|brazil|brasil|argentina"
)

# Remoto pero restringido a una región donde el usuario no puede trabajar.
UBIC_REMOTO_CERRADO = rf"""(?x)
    \b remote \s* [-–—(,/|]* \s* ({PAISES_CERRADOS}|{ESTADOS_EEUU})
  | \b ({PAISES_CERRADOS}) \s* [-–—(,/|]* \s* remote \b
  | \b remote \s* \( \s* ({PAISES_CERRADOS}|{ESTADOS_EEUU}) \s* \)
  | \b remote [-\s] friendly ,? \s* ({PAISES_CERRADOS})
  | \b remote \b [^|]{{0,28}}? \b ({ESTADOS_EEUU}) \s*,? \s* (usa|us\b|united\s+states)
  | \b (federal|skillbridge|govcloud|public\s+sector\s+us) \b
"""

# Remoto genuinamente abierto. Se evalúa SOLO sobre el campo de ubicación.
# 'north america' entra aquí porque México pertenece a Norteamérica, pero el
# sistema lo marca como "confirmar al postular": muchas empresas lo usan para
# decir "EEUU y Canadá".
UBIC_REMOTO_ABIERTO = r"""(?x)
    \b(worldwide|anywhere|globally|fully\s+distributed|globally\s+distributed)\b
  | \bremote\s*[-–—(,/|]*\s*(global|worldwide|anywhere|international)\b
  | \b(latam|latin\s+america|america\s+latina|latinoamerica|americas
      |north\s+america|norteamerica)\b
  | \bmexico\b | \bméxico\b | \bmexican\b
"""

# Ubicación que no aporta información de país: hay que mirar la descripción.
UBIC_GENERICA = r"""(?x)
    ^\s*(remote|remoto|remota|work\s+from\s+home|teletrabajo|distributed
      |virtual|home\s*-?\s*based|flexible|varios|multiple\s+locations|)\s*$
"""

# Ciudades/países donde una vacante presencial exigiría visa: no viable.
UBIC_EXTRANJERA = r"""(?x)
    \b(san\s+francisco|new\s+york|nyc\b|seattle|austin|boston|chicago|denver
    |los\s+angeles|washington|atlanta|dallas|houston|miami|toronto|vancouver
    |london|dublin|berlin|munich|paris|madrid|barcelona|amsterdam|zurich
    |stockholm|warsaw|krakow|lisbon|tel\s+aviv|bangalore|bengaluru|hyderabad
    |mumbai|delhi|pune|singapore|tokyo|sydney|melbourne|sao\s+paulo|são\s+paulo
    |buenos\s+aires|bogota|bogotá|lima|santiago|montevideo|san\s+jose,\s*costa)
"""

# Estados de México fuera del área metropolitana de Monterrey: presencial ahí
# implica mudarse, así que se marca aparte en vez de descartarse.
UBIC_MX_OTRA = r"""(?x)
    \b(ciudad\s+de\s+m|cdmx|distrito\s+federal|jalisco|guadalajara|queretaro
    |querétaro|puebla|tijuana|baja\s+california|chihuahua|sonora|hermosillo
    |aguascalientes|san\s+luis|merida|mérida|yucatan|cancun|veracruz|toluca
    |estado\s+de\s+m|leon,\s*guanajuato|guanajuato|saltillo|coahuila|torreon
    |tamaulipas|reynosa|matamoros|benito\s+juarez|cuauhtemoc|miguel\s+hidalgo
    |naucalpan|tlalnepantla|zapopan|tlaquepaque)
"""


# EJEMPLO. Logros con numeros verificables: la unica moneda que vale sin
# experiencia formal. Sustituye por los TUYOS. Un dato inventado en un correo
# te quema con el reclutador, asi que todo lo que el sistema afirme sale de
# esta lista: pon solo lo que puedas sostener. Conserva las tres areas como
# claves (las usa correos_frios.py).
LOGROS = {
    "ciberseguridad": [
        "EJEMPLO: diseñe un SGSI ISO 27001 completo con N entregables",
        "EJEMPLO: ejecute una auditoria interna con N hallazgos mapeados al Anexo A",
    ],
    "ia": [
        "EJEMPLO: describe aqui un proyecto medible de IA o seguridad de IA",
    ],
    "ti": [
        "EJEMPLO: describe aqui una tarea de TI o automatizacion que hiciste",
    ],
}

# Los MISMOS logros, escritos en ingles. Existe porque un correo en ingles no
# puede citar un logro escrito en espanol: se nota mas que quedarse corto. Si
# dejas un area vacia o en EJEMPLO, los correos en ingles hablaran de esa area
# como interes o estudio, sin afirmar que hiciste nada. Es lo correcto: mejor
# decir de menos que afirmar en un idioma lo que solo puedes sostener en otro.
LOGROS_EN = {
    "ciberseguridad": [
        "EXAMPLE: describe one security deliverable of yours, with its number",
    ],
    "ia": [
        "EXAMPLE: describe one AI or AI-security project of yours, and its metric",
    ],
    "ti": [
        "EXAMPLE: describe one IT or automation task you did",
    ],
}


# ---------------------------------------------------------------------------
# EJEMPLO. Pon SOLO las certificaciones que tengas. La division no es
# decorativa: 'pendientes' se nombran SIEMPRE con su estado. Presentar como
# obtenida una que no lo esta (un examen agendado y no presentado, por ejemplo)
# es el dato falso que quema una candidatura con una empresa para siempre.
CERTIFICACIONES = {
    "obtenidas": [
        ("EJEMPLO — Certificacion de ciberseguridad obtenida (Emisor)", "ciberseguridad"),
        ("EJEMPLO — Certificacion de IA obtenida (Emisor)", "ia"),
    ],
    # Nombrarlas SIEMPRE con su estado. Nunca a secas.
    "pendientes": [
        ("EJEMPLO — Certificacion en preparacion",
         "en preparacion, examen NO presentado"),
    ],
}


def certificaciones_de(area: str) -> list[str]:
    """Las certificaciones OBTENIDAS de un area. Nunca devuelve pendientes."""
    return [n for n, a in CERTIFICACIONES["obtenidas"] if a == area]


# ---------------------------------------------------------------------------
# EJEMPLO. Respuestas frecuentes de los formularios de una bolsa (OCC, Indeed,
# Computrabajo). Rellena con TUS datos.
#
# Los que valen None NO SE INVENTAN: `postular.py` se niega a rellenar un campo
# vacio y lo saca por pantalla para que lo decidas tu. Es la misma regla que
# rige los correos: un dato falso aqui queda por escrito en el expediente de la
# empresa. Deja en None lo que aun no hayas rellenado.
POSTULACION = {
    # Se derivan de CANDIDATO: edita alli tu identidad.
    "nombre": CANDIDATO["nombre"],
    "correo": CANDIDATO["correo"],
    "telefono": CANDIDATO["telefono"],
    "ciudad": "Monterrey, Nuevo Leon",
    "colonia": "",
    "pais": "Mexico",
    "nivel_estudios": "EJEMPLO — Licenciatura en curso",
    "semestre": None,                # se compara con el que exige el anuncio
    "carrera": "EJEMPLO — Tu carrera",
    "universidad": "EJEMPLO — Tu universidad",
    "titulado": False,
    "ingles": CANDIDATO["ingles"],
    # Declara tu experiencia real. 0 anios NO es 0 meses: seis meses de practicas
    # cuentan en muchos formularios, y decir "no" te los quita.
    "anios_experiencia": 0,
    "meses_experiencia": 0,
    "experiencia_texto": "EJEMPLO — resume tu experiencia (ver CV).",
    "linkedin": CANDIDATO["linkedin"],
    "github": CANDIDATO["github"],
    "requiere_visa_para_mexico": False,   # ajusta segun tu nacionalidad
    "disponibilidad_mudanza": False,

    "salario_esperado_mxn": None,
    "salario_texto": "EJEMPLO — indica tu expectativa salarial",
    "disponibilidad_horaria": "EJEMPLO — tu disponibilidad horaria",
    "fecha_inicio": "Inmediata",

    # Si tu facultad aun no te exige practicas obligatorias, ponlo en False: las
    # vacantes que exigen "carta de la universidad" o "convenio de practicas"
    # como REQUISITO no serian viables; las de becario abiertas a estudiantes
    # activos, si.
    "carta_de_la_universidad": False,
    "contexto_practicas": "EJEMPLO — describe tu situacion academica.",
}


def huecos_de_postulacion() -> list[str]:
    """Campos que faltan para poder postular sin inventar nada."""
    return [k for k, v in POSTULACION.items() if v is None]


# EJEMPLO. Nivel declarable por competencia y su justificacion, para los
# formularios que preguntan "Completa el nivel de conocimientos". Escala de las
# bolsas: ninguno, basico, medio, avanzado, experto. Declara SOLO lo que puedas
# sostener en una entrevista: decir "medio" en algo que no puedes defender quema
# la candidatura mas rapido que decir "basico". Sustituye por lo tuyo.
COMPETENCIAS = {
    "ciberseguridad": ("medio", "EJEMPLO: respaldalo con un logro concreto"),
    "iso 27001": ("basico", "EJEMPLO: describe tu experiencia real"),
    "grc": ("basico", "EJEMPLO: describe tu experiencia real"),
    "powershell": ("basico", "EJEMPLO: describe tu experiencia real"),
    "python": ("basico", "EJEMPLO: describe tu experiencia real"),
    "ingles": ("medio", "EJEMPLO: B2 conversacional; ajustalo a tu nivel"),
    # Sin respaldo ninguno: se responde "ninguno" y punto.
    "sql": ("ninguno", "no consta; no se inventa"),
    "sap": ("ninguno", "no consta; no se inventa"),
}


def nivel_de(competencia: str) -> tuple[str, str]:
    """Nivel declarable y su justificacion. ('ninguno', ...) si no consta."""
    from nucleo import sin_acentos
    clave = sin_acentos((competencia or "").lower()).strip()
    for k, v in COMPETENCIAS.items():
        if k in clave or clave in k:
            return v
    return ("ninguno", "no consta en perfil.py ni en el CV; no se inventa")

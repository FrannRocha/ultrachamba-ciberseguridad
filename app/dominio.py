"""
Clasificador de dominio: ¿de qué es realmente esta vacante?

Módulo autónomo. Responde una sola pregunta —si el puesto es de
ciberseguridad, de IA/datos, de TI general o de otro rubro— y la responde
mirando sobre todo el TÍTULO.

POR QUÉ EXISTE
--------------
El clasificador anterior dejaba pasar vacantes como "Mortgage
Processor/Underwriter", "Influencer Strategist" o "Mac MSP Help Desk Guru"
como si fueran de ciberseguridad. La causa era doble:

  1. Términos ambiguos ("audit", "risk", "compliance", "fraud", "identity")
     contaban como seguridad en cuanto el texto traía CUALQUIER palabra de
     contexto técnico, y esa lista incluía comodines como "datos", "data",
     "red", "it" o "sistemas". Casi cualquier anuncio los satisface.
  2. La DESCRIPCIÓN podía ascender una vacante de otro rubro: a un help desk
     que menciona phishing y cumplimiento le bastaba con acumular tres
     señales sueltas para volverse "ciberseguridad".

PRINCIPIO DE DISEÑO
-------------------
EL TÍTULO MANDA. Es lo único que la empresa eligió para nombrar el puesto.
La descripción solo puede confirmar (subir la confianza), matizar o dejar un
aviso en `motivos`, pero NUNCA convierte un puesto de otro rubro en uno de
seguridad. Un "Help Desk" que habla de phishing sigue siendo soporte.

ORDEN DE DECISIÓN (el primero que dispara, gana)
------------------------------------------------
  0. Veto de rubro ajeno en el título      -> 'fuera'
  1. Término inequívoco de seguridad y/o IA -> 'ciberseguridad' | 'ia' | 'ciber-ia'
  2. Término ambiguo + contexto ESTRICTO de TI, ambos en el título -> 'ciberseguridad'
  3. Familia de soporte/mesa de ayuda      -> 'ti-general'
  4. Contexto de TI en el título           -> 'ti-general'
  5. Descripción claramente de TI          -> 'ti-general' (confianza baja)
  6. Nada de lo anterior                   -> 'fuera'

API pública: `clasificar_dominio(titulo, descripcion) -> dict`.
"""
from __future__ import annotations

from nucleo import normalizar, terminos_presentes

# --------------------------------------------------------------------------
# 0. RUBROS AJENOS — veto que gana sobre cualquier otra señal del título.
# --------------------------------------------------------------------------
# Criterio: si la empresa nombró OTRO oficio en el título, el puesto es de ese
# oficio. Da igual que la descripción hable de seguridad; en el mejor de los
# casos el usuario sería el becario de contabilidad que además ve un firewall.
#
# El sufijo '*' es coincidencia por prefijo (ver `nucleo.tiene_termino`).
# Se buscan con límites de palabra, así que 'produccion' NO casa con
# 'producto' ni 'ventas' con 'preventa'.

# a) Finanzas, contabilidad, seguros y actuaría. Es el falso positivo más caro:
#    comparten TODO el vocabulario ambiguo (auditoria, riesgo, control interno).
AJENO_FINANZAS = [
    "fiscal", "contable*", "contabilidad", "contadur*", "impuestos", "tax",
    "actuari*", "actuarial", "seguros", "insurance", "siniestros", "claims",
    "nomina", "payroll", "tesoreria", "treasury", "cobranza", "collections",
    "credito", "crediticio", "credit", "financier*", "finanzas",
    "financial", "finance", "balances", "facturacion", "accounting", "accountant*",
    "hipotecas", "hipotecario", "mortgage", "underwriter", "underwriting",
    "prestamos", "lending", "banca patrimonial", "inversiones", "trading",
    # "Practicante de Rentabilidad" (DEACERO) llego a recomendarse con 69
    # puntos. Rentabilidad, costos y presupuesto son finanzas, no TI.
    "rentabilidad", "costos", "presupuesto*", "utilidades", "margenes",
    "cuentas por pagar", "cuentas por cobrar", "conciliacion*",
]

# b) Roles de negocio: aunque el producto sea ciberseguridad, el trabajo es
#    vender, reclutar o comunicar. No es lo que el usuario busca.
AJENO_NEGOCIO = [
    "ventas", "sales", "comercial", "account executive", "account manager",
    "ejecutivo de cuenta", "business development", "desarrollo de negocio",
    "preventa", "pre-sales", "customer success", "marketing", "mercadotecnia",
    "influencer", "redes sociales", "social media", "community manager",
    "publicidad", "branding", "ecommerce", "pricing",
]

# c) Recursos humanos y formación.
AJENO_PERSONAS = [
    "reclutamiento", "reclutador*", "recruiter", "recruiting", "recruitment",
    "recursos humanos", "human resources", "capital humano",
    "talent acquisition", "atraccion de talento", "integracion de talento",
    "capacitacion", "capacitador*", "entrenador*", "instructor*", "docente",
    "profesor*", "maestro", "trainer",
]

# d) Otras seguridades: industrial, física, patrimonial. Comparten la palabra
#    'seguridad' con la ciberseguridad y nada más.
AJENO_SEGURIDAD_NO_TI = [
    "seguridad industrial", "seguridad e higiene", "higiene y seguridad",
    "seguridad patrimonial", "seguridad fisica", "physical security",
    "seguridad privada", "vigilancia", "guardia", "custodio", "proteccion civil",
    "seguridad del paciente", "seguridad alimentaria",
    # El veto estaba solo en español y dejaba entrar 21 vacantes de guardias de
    # Allied Universal clasificadas como CIBERSEGURIDAD, porque 'security' es
    # termino fuerte. Estas frases son inequivocas: ningun puesto de seguridad
    # informatica se llama asi.
    "security guard", "armed security", "unarmed security", "event security",
    "security patrol", "patrol officer", "crowd control",
    "bodyguard", "gate guard", "flex officer", "escolta", "guard card",
]

# 'Security Officer' es el titulo estandar del guardia en EE.UU., pero tambien
# la cola de 'Information Security Officer' y 'Information System Security
# Officer (ISSO)', que si son ciberseguridad de verdad. No se puede vetar a
# secas ni dejar pasar a secas: decide el calificador que lo acompana.
# 'loss prevention' vive aqui y no en la lista dura por la misma razon: solo
# es el guardia de tienda cuando va suelto. 'Data Loss Prevention' (DLP) es
# ciberseguridad pura, y meterlo en el veto duro tiro una vacante legitima.
GUARDIA_SI_NO_HAY_CALIFICADOR = [
    "security officer", "security operative", "security agent", "safety officer",
    "loss prevention",
]

CALIFICADOR_INFORMATICO = [
    "information", "informacion", "cyber*", "ciber*", "infosec", "ti", "it",
    "sistemas", "system*", "digital", "red*", "network*", "datos", "data",
    "software", "aplicaciones", "cloud", "informatic*", "tecnologic*",
]

# e) Operaciones, planta y otros oficios sin relación con TI.
AJENO_OPERACIONES = [
    # Tercera reincidencia del mismo patron: el veto estaba solo en español.
    # 'manufactura' vetada pero 'manufacturing' no; 'logistica' vetada pero
    # 'logisticos' tampoco, por no llevar el sufijo de prefijo. Se colaban
    # "Manufacturing intern" (Schneider) y "Becario Sistemas Logisticos".
    "logistic*", "manufacturing", "promociones", "mercancia*",
    "practicante de administracion", "becario de administracion",
    "auxiliar administrativo", "administrativo", "administrativa",
    "logistica", "almacen", "inventarios", "compras", "abastecimiento",
    "produccion", "manufactura", "planta", "calidad", "ambiental",
    "electromecanic*", "automotriz", "construccion", "obra civil",
    "mantenimiento industrial", "enfermeria", "medico", "clinico",
    # Mismo hueco de idioma que en seguridad fisica: el rubro salud solo estaba
    # vetado en español y entraban 'Nurse Educator', 'Clinical Support
    # Specialist' o 'Fractional Clinical Nursing Informaticist'.
    "nurse*", "nursing", "clinical", "medicare", "medicaid", "paciente*",
    "farmac*", "legal", "juridic*", "counsel", "abogad*", "notarial",
    "atencion a clientes", "atencion al cliente", "call center", "callcenter",
    "servicio al cliente", "customer service", "telemarketing", "cajero",
    "recepcionista", "chofer", "operador de montacargas",
]

DOMINIO_AJENO = (
    AJENO_FINANZAS + AJENO_NEGOCIO + AJENO_PERSONAS
    + AJENO_SEGURIDAD_NO_TI + AJENO_OPERACIONES
)

# NOTA sobre "help desk", "mesa de ayuda" y "soporte tecnico":
# la especificación los listaba junto a los rubros ajenos, pero AQUÍ NO SON
# VETO. Criterio adoptado: el soporte técnico es la puerta de entrada real a
# TI para un estudiante de Seguridad en TI (y varias vacantes de SOC N1 se
# publican con ese nombre), así que se clasifican como 'ti-general': visibles,
# pero nunca confundidos con ciberseguridad. Como el veto de rubro ajeno se
# evalúa ANTES, un título que los combine con otro oficio ("Help Desk Call
# Center", "Mesa de ayuda de nomina") sí termina en 'fuera'.
TI_SOPORTE = [
    "help desk", "helpdesk", "service desk", "servicedesk", "mesa de ayuda",
    "mesa de servicio", "soporte tecnico", "soporte a usuarios",
    "soporte de ti", "soporte en sitio", "desktop support", "technical support",
    "it support", "user support", "field service", "soporte",
]

# --------------------------------------------------------------------------
# 1. TÉRMINOS INEQUÍVOCOS
# --------------------------------------------------------------------------
# Si uno de estos aparece en el TÍTULO, la vacante es de ciberseguridad.
# Ninguno tiene un uso frecuente en otro rubro.
# Ojo: 'security' va exacto, no como prefijo: 'securit*' casaría con
# 'securities' (finanzas).
CIBER_FUERTE = [
    "ciber*", "cyber*", "infosec", "security", "appsec", "devsecops", "secops",
    "seguridad de la informacion", "seguridad informatica",
    "information security", "seguridad ofensiva", "seguridad defensiva",
    "soc", "siem", "soar", "edr", "xdr", "dlp", "iam", "pki",
    "pentest*", "penetration test*", "ethical hack*", "hacking etico",
    "hacking", "hacker*", "bug bounty",
    "red team", "blue team", "purple team",
    "malware", "ransomware", "phishing", "forense", "forensic*",
    "threat*", "amenaza*", "vulnerabilidad*", "vulnerabilit*",
    "ciso", "grc", "governance, risk", "gobierno, riesgo",
    "iso 27001", "iso/iec 27001", "27001", "iso 42001",
    "nist", "owasp", "mitre", "zero trust", "hardening",
    "incident response", "respuesta a incidentes", "criptograf*", "cryptograph*",
    # Huecos que destapo la limpieza de las descripciones: sin ellos, un
    # "Ingeniero de Identidad y Acceso" (que es IAM puro) quedaba fuera porque
    # 'identidad' sola es un termino ambiguo.
    "identidad y acceso", "gestion de identidades", "identity and access",
    "control de acceso", "access management", "privileged access",
    "acceso privilegiado", "pam", "sso", "mfa", "autenticacion",
    "ai safety", "seguridad de la ia", "trust and safety",
    "llm security", "prompt injection", "jailbreak", "guardrails",
]

# Igual, pero para IA / datos. También son inequívocos en un título.
IA_FUERTE = [
    "ia", "ai", "inteligencia artificial", "artificial intelligence",
    "machine learning", "aprendizaje automatico", "deep learning",
    "redes neuronales", "neural",
    # OJO: el comodin '*' solo funciona al FINAL del termino, nunca en medio.
    # "ingenier* de datos" y "cientific* de datos" estaban escritos asi y no
    # coincidian con nada: "Practicante de Ingenieria de Datos" salia
    # clasificada como fuera. Se escriben las variantes completas.
    "data scien*", "ciencia de datos", "cientifico de datos",
    "cientifica de datos", "cientificos de datos",
    "data engineer*", "ingenieria de datos", "ingeniero de datos",
    "ingeniera de datos", "practicante de datos", "becario de datos",
    "data analyst", "analista de datos",
    "analitica de datos", "analitica avanzada", "data analytics",
    "gobierno de datos", "data governance",
    "llm", "llms", "language model", "modelo de lenguaje",
    "nlp", "procesamiento de lenguaje", "mlops", "genai", "gen ai",
    "generative ai", "ia generativa", "computer vision", "vision artificial",
    "interpretability", "interpretabilidad", "rlhf", "big data",
]

# --------------------------------------------------------------------------
# 2. TÉRMINOS AMBIGUOS Y SU CONTEXTO
# --------------------------------------------------------------------------
# Estos existen idénticos en auditoría contable, riesgo financiero, actuaría y
# cumplimiento legal. Solo acreditan ciberseguridad si el MISMO TÍTULO trae
# contexto tecnológico explícito.
AMBIGUOS = [
    "auditoria", "auditor*", "audit", "auditing",
    "riesgo*", "risk", "compliance", "cumplimiento", "control interno",
    "internal control", "governance", "gobierno", "identidad", "identity",
    "fraude*", "fraud", "privacidad", "privacy", "deteccion", "detection",
    "incidente*", "regulatorio", "normativ*",
]

# Contexto ESTRICTO: lo único que convierte un término ambiguo en seguridad.
# Deliberadamente NO incluye 'datos', 'data' ni 'red': esos comodines eran la
# causa raíz de que "Becario de Auditoría Fiscal y Análisis de Bases de Datos"
# puntuara como vacante de ciberseguridad.
CONTEXTO_ESTRICTO = [
    "ti", "it", "sistemas", "sistemas de informacion", "informatica",
    "informatic*", "tecnologia de la informacion", "tecnologias de la informacion",
    "information technology", "itgc", "sox", "de la informacion",
    "cibernetic*", "digital", "tecnologic*", "tecnologia*", "tech",
    "software", "aplicaciones", "cloud", "ciberseguridad",
]

# 'seguridad' a secas es demasiado suelta en español para ser inequívoca, pero
# sus falsos positivos (industrial, patrimonial, física, e higiene) ya se van
# en el veto de rubro ajeno. Por eso le basta con contexto de TI amplio, y no
# con el estricto que se exige a 'auditoria' o 'riesgo'.
SEGURIDAD_GENERICA = ["seguridad", "safety"]

# --------------------------------------------------------------------------
# 3. CONTEXTO DE TI GENERAL (regla 6)
# --------------------------------------------------------------------------
# Amplio a propósito: aquí no se otorga 'ciberseguridad', solo 'ti-general'.
# 'red' en singular queda fuera (casa con "redes sociales", "red de tiendas").
CONTEXTO_TI = [
    "ti", "it", "sistemas", "informatica", "informatic*", "computacion",
    "computo", "telecomunicaciones", "telematica", "tecnologia*", "tech",
    "infraestructura", "infrastructure", "redes", "network*", "cloud", "nube",
    "devops", "sre", "site reliability", "sysadmin", "administrador de sistemas",
    "servidores", "server*", "data center", "datacenter", "erp", "sap",
    "software", "hardware", "developer", "desarrollador*", "programador*",
    "desarrollo de software", "full stack", "backend", "back end", "frontend",
    "python", "java", "javascript", ".net", "sql", "base de datos", "dba",
    "linux", "windows server", "azure", "aws", "google cloud", "open source",
    "centro de datos", "centros de datos",   # la version en español de 'data center'
    "helpdesk", "help desk", "service desk", "mesa de ayuda", "mesa de servicio",
    "soporte", "activos ti", "gestion de activos",
]

# --------------------------------------------------------------------------
# Confianzas base de cada camino de decisión.
# --------------------------------------------------------------------------
_CONF = {
    "veto": 0.93,
    "fuerte": 0.88,
    "cruce": 0.90,
    "ambiguo_ctx": 0.72,
    "seguridad_ctx": 0.70,
    "soporte": 0.80,
    "ti_ctx": 0.72,
    "ti_desc": 0.45,
    "fuera": 0.62,
    "fuera_ambiguo": 0.66,
}

_AREAS = ("ciberseguridad", "ia", "ciber-ia", "ti-general", "fuera")


def _presentes(texto_n: str, vocabulario) -> list[str]:
    """Términos del vocabulario presentes como palabra completa."""
    if not texto_n:
        return []
    return terminos_presentes(texto_n, vocabulario)


def _ev(origen: str, terminos) -> list[str]:
    """Formatea evidencia legible: de dónde salió cada término."""
    return [f"{origen}: {t}" for t in terminos]


def _ajustar(confianza: float, delta: float) -> float:
    return round(max(0.20, min(0.97, confianza + delta)), 2)


def _resultado(area: str, confianza: float, evidencia: list[str],
               motivos: list[str]) -> dict:
    assert area in _AREAS, f"area invalida: {area}"
    return {
        "area": area,
        "confianza": round(float(confianza), 2),
        "evidencia": evidencia,
        "motivos": motivos,
    }


def clasificar_dominio(titulo: str, descripcion: str) -> dict:
    """Devuelve {'area', 'confianza', 'evidencia', 'motivos'}.

    `area` es uno de: 'ciberseguridad', 'ia', 'ciber-ia', 'ti-general', 'fuera'.
    `confianza` va de 0.0 a 1.0. `evidencia` son los términos concretos que
    dispararon el veredicto. `motivos` explica la decisión en español sin
    acentos, para que el usuario pueda auditar por qué el sistema decidió eso.
    """
    titulo_n = normalizar(titulo or "")
    desc_n = normalizar(descripcion or "")[:4000]

    if not titulo_n.strip():
        return _resultado(
            "fuera", 0.30, [],
            ["sin titulo: el titulo es la unica senal fiable y no hay ninguna"],
        )

    # Señales del título, calculadas una sola vez.
    ajenos = _presentes(titulo_n, DOMINIO_AJENO)
    t_ciber = _presentes(titulo_n, CIBER_FUERTE)
    t_ia = _presentes(titulo_n, IA_FUERTE)
    t_ambiguo = _presentes(titulo_n, AMBIGUOS)
    t_seguridad = _presentes(titulo_n, SEGURIDAD_GENERICA)
    t_soporte = _presentes(titulo_n, TI_SOPORTE)

    # Señales de la descripción: solo modulan la confianza y dejan avisos.
    d_ciber = _presentes(desc_n, CIBER_FUERTE)
    d_ia = _presentes(desc_n, IA_FUERTE)
    d_ti = _presentes(desc_n, CONTEXTO_TI)

    # --------------------------------------------------------------- 0a ----
    # Guardia de seguridad fisica disfrazado. 'Security Officer' sin ningun
    # calificador informatico es el guardia; con 'Information' delante es el
    # ISSO/CISO, que si es del oficio. Va antes del veto general porque la
    # decision depende de lo que ACOMPANA al termino, no del termino solo.
    guardia = _presentes(titulo_n, GUARDIA_SI_NO_HAY_CALIFICADOR)
    if guardia:
        calificador = _presentes(titulo_n, CALIFICADOR_INFORMATICO)
        if not calificador:
            return _resultado(
                "fuera", _CONF["veto"], _ev("titulo", guardia),
                [f"'{guardia[0]}' sin nada informatico al lado es el titulo del "
                 "guardia de seguridad fisica, no de seguridad informatica",
                 "si fuera del oficio diria 'information security officer', "
                 "'ciso' o 'seguridad de la informacion'"],
            )

    # ---------------------------------------------------------------- 0 ----
    # Veto de rubro ajeno: gana sobre todo, incluso sobre un termino fuerte de
    # seguridad en el mismo titulo. "Becario Comercial de Ciberseguridad" es
    # una vacante de ventas que vende ciberseguridad.
    if ajenos:
        motivos = [
            f"el titulo nombra otro rubro: '{ajenos[0]}'; ese oficio manda "
            "sobre cualquier palabra de seguridad o IA que traiga el texto"
        ]
        if t_ciber or t_ia:
            mezcla = (t_ciber + t_ia)[0]
            motivos.append(
                f"el titulo mezcla '{mezcla}' con '{ajenos[0]}': se descarta "
                "porque el puesto pertenece al otro rubro, no a seguridad"
            )
        if d_ciber:
            motivos.append(
                "la descripcion menciona seguridad, pero una descripcion no "
                "cambia el rubro del puesto"
            )
        confianza = _ajustar(_CONF["veto"], 0.03 * (len(ajenos) - 1))
        return _resultado("fuera", confianza, _ev("titulo", ajenos), motivos)

    # ---------------------------------------------------------------- 1 ----
    # Terminos inequivocos en el titulo.
    if t_ciber and t_ia:
        confianza = _CONF["cruce"]
        motivos = [
            f"el titulo cruza seguridad e IA: '{t_ciber[0]}' + '{t_ia[0]}'",
            "cruce IA+seguridad: es exactamente el diferenciador del perfil",
        ]
        if d_ciber and d_ia:
            confianza = _ajustar(confianza, 0.05)
            motivos.append("la descripcion confirma ambos lados del cruce")
        return _resultado(
            "ciber-ia", confianza,
            _ev("titulo", t_ciber) + _ev("titulo", t_ia), motivos,
        )

    if t_ciber:
        confianza = _CONF["fuerte"]
        motivos = [f"termino inequivoco de seguridad en el titulo: '{t_ciber[0]}'"]
        evidencia = _ev("titulo", t_ciber)
        if len(d_ciber) >= 3:
            confianza = _ajustar(confianza, 0.06)
            motivos.append(f"la descripcion lo confirma ({len(d_ciber)} senales)")
            evidencia += _ev("descripcion", d_ciber[:5])
        elif not desc_n:
            confianza = _ajustar(confianza, -0.05)
            motivos.append("sin descripcion para confirmar: veredicto solo por titulo")
        return _resultado("ciberseguridad", confianza, evidencia, motivos)

    if t_ia:
        confianza = _CONF["fuerte"]
        motivos = [f"termino inequivoco de IA/datos en el titulo: '{t_ia[0]}'"]
        evidencia = _ev("titulo", t_ia)
        if t_ambiguo:
            motivos.append(
                f"el titulo tambien trae '{t_ambiguo[0]}', que es ambiguo: "
                "confirma que el analisis sea tecnico y no financiero"
            )
            confianza = _ajustar(confianza, -0.08)
        if len(d_ia) >= 3:
            confianza = _ajustar(confianza, 0.06)
            motivos.append(f"la descripcion lo confirma ({len(d_ia)} senales)")
            evidencia += _ev("descripcion", d_ia[:5])
        elif not desc_n:
            confianza = _ajustar(confianza, -0.05)
            motivos.append("sin descripcion para confirmar: veredicto solo por titulo")
        return _resultado("ia", confianza, evidencia, motivos)

    # ---------------------------------------------------------------- 2 ----
    # Termino ambiguo + contexto tecnologico ESTRICTO, ambos en el titulo.
    if t_ambiguo:
        ctx = _presentes(titulo_n, CONTEXTO_ESTRICTO)
        if ctx:
            confianza = _CONF["ambiguo_ctx"]
            motivos = [
                f"'{t_ambiguo[0]}' es ambiguo, pero el titulo lo ancla a "
                f"tecnologia con '{ctx[0]}': es auditoria/riesgo de TI"
            ]
            evidencia = _ev("titulo", t_ambiguo) + _ev("contexto", ctx)
            if len(d_ciber) >= 3:
                confianza = _ajustar(confianza, 0.08)
                motivos.append(
                    f"la descripcion refuerza el enfoque de seguridad ({len(d_ciber)} senales)"
                )
            return _resultado("ciberseguridad", confianza, evidencia, motivos)

    # 'seguridad' a secas: le basta contexto de TI amplio (ver comentario del
    # vocabulario). "Ingeniero Junior Redes y Seguridad" si es ciberseguridad.
    if t_seguridad:
        ctx_ti = _presentes(titulo_n, CONTEXTO_TI)
        if ctx_ti:
            motivos = [
                f"el titulo dice 'seguridad' junto a contexto de TI ('{ctx_ti[0]}'): "
                "es seguridad informatica, no industrial ni patrimonial"
            ]
            return _resultado(
                "ciberseguridad", _CONF["seguridad_ctx"],
                _ev("titulo", t_seguridad) + _ev("contexto", ctx_ti), motivos,
            )

    # ---------------------------------------------------------------- 3 ----
    # Familia de soporte / mesa de ayuda: TI general, nunca ciberseguridad.
    if t_soporte:
        motivos = [
            f"el titulo es de soporte ('{t_soporte[0]}'): puerta de entrada a TI, "
            "no es un puesto de ciberseguridad"
        ]
        if d_ciber:
            motivos.append(
                f"la descripcion menciona seguridad ({', '.join(d_ciber[:3])}) pero "
                "no asciende el puesto: un help desk sigue siendo soporte"
            )
        return _resultado(
            "ti-general", _CONF["soporte"], _ev("titulo", t_soporte), motivos,
        )

    # ---------------------------------------------------------------- 4 ----
    # Contexto de TI en el titulo, sin especialidad declarada.
    ctx_ti = _presentes(titulo_n, CONTEXTO_TI)
    if ctx_ti:
        motivos = [
            f"titulo de TI general ('{ctx_ti[0]}') sin especialidad de seguridad ni IA"
        ]
        if d_ciber:
            motivos.append(
                "la descripcion toca seguridad, pero el titulo manda: se queda en TI general"
            )
        return _resultado(
            "ti-general", _CONF["ti_ctx"], _ev("titulo", ctx_ti), motivos,
        )

    # ---------------------------------------------------------------- 5 ----
    # Ultimo recurso: el titulo no dice nada y la descripcion es claramente de
    # TI. Solo puede llegar a 'ti-general', jamas a seguridad ni a IA.
    if len(d_ti) >= 3:
        motivos = [
            "el titulo no declara area; la descripcion apunta a TI "
            f"({len(d_ti)} senales): clasificada como TI general con baja confianza"
        ]
        if d_ciber:
            motivos.append(
                "hay menciones de seguridad en la descripcion, pero sin respaldo "
                "en el titulo no se clasifica como ciberseguridad"
            )
        return _resultado(
            "ti-general", _CONF["ti_desc"], _ev("descripcion", d_ti[:5]), motivos,
        )

    # ---------------------------------------------------------------- 6 ----
    if t_ambiguo:
        motivos = [
            f"el titulo solo trae terminos ambiguos ('{t_ambiguo[0]}') sin contexto "
            "de TI: puede ser auditoria contable, riesgo financiero o actuarial"
        ]
        return _resultado(
            "fuera", _CONF["fuera_ambiguo"], _ev("titulo", t_ambiguo), motivos,
        )

    motivos = ["el titulo no es de seguridad, ni de IA, ni de TI"]
    if d_ciber or d_ia:
        motivos.append(
            "la descripcion menciona el tema, pero sin senal en el titulo no alcanza"
        )
    return _resultado("fuera", _CONF["fuera"], [], motivos)

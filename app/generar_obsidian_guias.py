"""
Notas de guía de la bóveda: el plan de acción, los correos y la preparación.

Se separa de `generar_obsidian.py` por la regla "una nota = un tema" aplicada
al propio código: aquí vive el contenido estratégico, allí la maquinaria.
"""
from __future__ import annotations

from almacen import cifras_panel, conexion
from generar_obsidian import ctx, nota
from perfil import CANDIDATO


def ultima_corrida() -> dict:
    """La ultima corrida, contada contra la base.

    Existe porque `estadisticas.json` publicaba `crudas: 133579` y
    `vivas: 2228`, y ninguna de las dos se puede comprobar: `corridas.crudas`
    es NULL en las 11 corridas y ese 2.228 era en realidad `guardadas`.
    """
    with conexion() as con:
        f = con.execute("SELECT * FROM corridas ORDER BY rowid DESC LIMIT 1").fetchone()
        return dict(f) if f else {"guardadas": 0, "nuevas": 0, "inicio": ""}


def notas_guias(est: dict, vacantes: list[dict]) -> None:
    _mejorar_el_cv()
    _plan_30_dias()
    _correos()
    _linkedin_github()
    _entrevista_ingles()
    _empresas_objetivo(vacantes)
    _como_usar_el_sistema(est)
    _cuanto_ahorra_la_boveda()


# ---------------------------------------------------------------------------

def _mejorar_el_cv() -> None:
    nota(
        "guias/mejorar-el-cv",
        "Mejorar el CV: lo que dicen los datos",
        "guia", "pendiente",
        ctx("que cambiar en el CV, con la evidencia que respalda cada cambio")
        + """
## Para que sirve esta nota

Aqui va TU plan de mejora del CV. Esta version del proyecto se comparte sin el
CV de nadie, asi que la nota viene sin diagnostico a proposito: no hay uno que
puedas heredar de otra persona.

## Como hacerte el diagnostico

1. **Comprueba que tu PDF se lee a maquina.** Abrelo y copia el texto: si al
   pegarlo salen las letras separadas, las columnas mezcladas o los apartados
   fuera de orden, un parseador automatico lo leera igual de mal. Suele ser el
   defecto mas caro y el mas barato de arreglar: una sola columna, encabezados
   sin espaciado entre letras, y sin miedo a dos paginas.

2. **Cuenta que piden de verdad los anuncios de TU base.** Cuando tengas una
   recoleccion hecha, `app/analisis_mercado.py` compara los terminos que salen
   en las vacantes con lo que tu perfil acredita. Ese hueco, medido contra tus
   propios datos, vale mas que cualquier lista de consejos de internet.

3. **Cuantifica lo que ya hiciste.** Cada punto de experiencia empieza con un
   verbo y termina en un numero: "ejecute la auditoria interna: N hallazgos
   mapeados al Anexo A" dice mas que "conocimientos de auditoria".

4. **No declares lo que no puedas sostener.** Una certificacion en preparacion
   se nombra con su estado, y un nivel de idioma con su etiqueta real. Lo que
   no aguante una entrevista, fuera.

## Que NO hacer

Copiar los logros de otra persona. Todo lo que afirmes aqui y en los correos
sale de `app/perfil.py`, y ese archivo lo rellenas tu.
""",
        ["[[perfil/perfil-del-candidato]]", "[[perfil/brechas-y-como-cerrarlas]]",
         "[[guias/optimizar-linkedin-y-github]]", "[[01-wiki]]"],
        "Guias de accion", "Mejorar el CV: lo que dicen los datos",
    )


# ---------------------------------------------------------------------------

def _plan_30_dias() -> None:
    nota(
        "guias/plan-de-accion-30-dias",
        "Plan de accion de 30 dias",
        "guia", "pendiente",
        ctx("el plan concreto de que hacer cada semana para conseguir las practicas")
        + """
## La idea que ordena todo el plan

Postular por formulario tiene una tasa de respuesta baja y no depende de ti.
Escribir a una persona concreta tiene una tasa mucho mas alta y si depende de
ti. **El formulario es el tramite; el correo es la candidatura.** Por eso cada
semana de este plan mezcla ambos, con mas peso en el contacto humano.

## Semana 1 — Municion

- [ ] Abrir `dashboard.html` y filtrar por **Prioridad: Aplicar ya** + **Monterrey**.
      Marcar las 10 que mas te interesen.
- [ ] Reescribir el titular del CV segun a que apuntes. Si mandas a GRC, que
      diga GRC. Si mandas a SOC, que diga SOC. Un CV generico compite peor.
- [ ] Rehacer el README de tu mejor proyecto
      (ver [[guias/optimizar-linkedin-y-github]]). Suele ser el activo peor
      vendido: el codigo esta, la explicacion no.
- [ ] Actualizar LinkedIn: titular, "Acerca de" y proyectos.
- [ ] Preparar los tres correos base de [[guias/correos-de-postulacion]].

## Semana 2 — Primer lote

- [ ] Postular a las 10 marcadas, **cada una con su correo directo**.
      Formulario + correo a una persona. Siempre las dos cosas.
- [ ] Escribir a 5 personas de [[guias/empresas-objetivo-en-monterrey]] aunque
      no tengan vacante publicada. Las practicas suelen crearse cuando llega
      un buen candidato, no al reves.
- [ ] Hablar con la coordinacion de tu carrera y preguntar explicitamente
      que convenios de practicas tiene la facultad. Es la via mas corta y la
      que casi nadie usa.
- [ ] Registrar cada envio marcando la vacante como aplicada en el dashboard.

## Semana 3 — Ampliar y demostrar

- [ ] Levantar el laboratorio de Sentinel y escribir 5 reglas KQL propias.
      Publicarlas en GitHub. Esto ataca directamente la brecha mas cara de
      [[perfil/brechas-y-como-cerrarlas]].
- [ ] Postular a 10 vacantes remotas de la lista, priorizando las que digan
      LatAm o Mexico.
- [ ] Publicar en LinkedIn una explicacion corta de algo que ya hiciste: como
      lo construiste, o que aprendiste cuando se rompio. Un post concreto vale
      mas que veinte solicitudes de contacto.
- [ ] Hacer seguimiento de los correos de la semana 2 que no respondieron.
      Un unico recordatorio breve, a los 7 dias.

## Semana 4 — Cerrar

- [ ] Segundo lote: 10 postulaciones mas.
- [ ] Presentar la SC-200 si ya esta lista. Aprobarla cambia como te lee un filtro.
- [ ] Preparar el relato en ingles de tus tres logros principales
      ([[guias/entrevista-tecnica-en-ingles]]).
- [ ] Re-ejecutar el pipeline para traer vacantes nuevas:
      `python app/pipeline.py && python app/generar_dashboard.py`

## Numeros a los que apuntar

| Metrica | Objetivo en 30 dias |
|---|---|
| Postulaciones con correo directo | 25-30 |
| Personas contactadas sin vacante publicada | 15 |
| Respuestas esperables | 4-8 |
| Entrevistas esperables | 2-4 |

Si al terminar el mes tienes menos de 3 respuestas, el problema casi siempre
esta en el CV o en el correo de apertura, no en la cantidad. Revisa
[[guias/correos-de-postulacion]] antes de subir el volumen.
""",
        ["[[guias/correos-de-postulacion]]", "[[perfil/brechas-y-como-cerrarlas]]",
         "[[guias/empresas-objetivo-en-monterrey]]", "[[01-wiki]]"],
        "Guias de accion", "Plan de accion de 30 dias",
    )


# ---------------------------------------------------------------------------

def _correos() -> None:
    nota(
        "guias/correos-de-postulacion",
        "Correos de postulacion",
        "guia", "pendiente",
        ctx("las plantillas de correo listas para enviar, con la logica detras")
        + f"""
## Las tres reglas que hacen que un correo se lea

1. **El asunto dice quien eres y que quieres.** Nada de "Solicitud de empleo".
2. **La primera linea trae un hecho concreto, no una presentacion.** Un
   reclutador decide en la primera frase si sigue leyendo.
3. **Un solo pedido claro al final.** No "quedo a sus ordenes": una pregunta
   concreta que se pueda responder con si o no.

## A quien escribir

Por orden de efectividad:

1. La persona que seria tu jefe (lider de seguridad, gerente de TI, CISO).
2. El reclutador tecnico de la empresa.
3. Recursos Humanos generico. Ultimo recurso.

Como encontrar el correo: LinkedIn para el nombre, y luego el patron de la
empresa (`nombre.apellido@empresa.com` suele ser el patron mas comun en
corporativos mexicanos). Si no lo encuentras, el mensaje directo por LinkedIn
funciona casi igual de bien.

---

> Estas plantillas son EJEMPLOS. Sustituye lo que va entre [corchetes] por lo
> tuyo y no afirmes ningun logro que no puedas sostener.

## Plantilla 1 — Practicas de ciberseguridad en Monterrey (espanol)

> **Asunto:** Practicante de ciberseguridad — construi un SGSI ISO 27001 completo

Hola [Nombre]:

Soy [tu nombre], estudiante de [tu carrera] en [tu universidad]. [Sustituye
esto por UN logro concreto y verificable tuyo. El estilo que funciona es un
hecho medible, no una presentacion: p. ej. "construi desde cero un SGSI
alineado a ISO/IEC 27001:2022 con N entregables y ejecute la auditoria interna,
con N hallazgos mapeados al Anexo A". No afirmes nada que no puedas sostener.]

Vi que [empresa] [razon concreta: la vacante de X / que estan creciendo el area
de seguridad / el proyecto Y]. Me gustaria hacer mis practicas con ustedes.
Puedo aportar desde el primer dia en documentacion de seguridad, respuesta a
incidentes y automatizacion con PowerShell.

Adjunto mi CV. ¿Tendrian 15 minutos esta semana o la proxima para platicar?

{CANDIDATO['nombre']}
{CANDIDATO['telefono']} · {CANDIDATO['correo']}
{CANDIDATO['github']} · {CANDIDATO['linkedin']}

---

## Plantilla 2 — Seguridad de IA (ingles)

> **Asunto:** Security internship — [EXAMPLE: your measurable AI-security result]

Hi [Name],

I'm a [your field] student at [your university] in [your city]. [Replace this
with ONE concrete, verifiable project of yours. The style that works is a
measurable fact, e.g. "I built a ~N-line tool that does X, with a test suite
that scores each change against a metric." Do not claim anything you cannot
back up.]

[Optional second proof point, e.g. a defensive project you actually did: an
ISO/IEC 27001 ISMS you built, an internal audit you ran. Keep it concrete and
true.]

I'd like to apply for [role]. I'm based in Monterrey (UTC-6, overlapping US
hours) and available [X] hours per week.

Would you be open to a short call?

Best,
{CANDIDATO['nombre']}
{CANDIDATO['github']} · {CANDIDATO['linkedin']}

---

## Plantilla 3 — Candidatura espontanea, sin vacante publicada

> **Asunto:** ¿Reciben practicantes en el area de seguridad? — perfil GRC + Blue Team

Hola [Nombre]:

No vi una vacante publicada de practicas en seguridad en [empresa], pero
prefiero preguntar directo.

Soy estudiante de [tu carrera] en [tu universidad]. [Resume en una o dos lineas
lo que YA hiciste, concreto y verificable. Ejemplo: un SGSI alineado a ISO
27001:2022, una auditoria interna con N hallazgos, un runbook de respuesta a
incidentes, automatizacion en PowerShell.]

Si en algun momento abren practicas en seguridad, TI o cumplimiento, me
encantaria que me consideraran. Y si hoy no es el momento, ¿me podria decir a
quien conviene escribirle?

Gracias por el tiempo,
{CANDIDATO['nombre']}
{CANDIDATO['telefono']} · {CANDIDATO['correo']}

---

## Plantilla 4 — Seguimiento a los 7 dias

> **Asunto:** Re: [asunto original]

Hola [Nombre]:

Le escribo solo para poner mi correo de nuevo arriba de su bandeja, por si se
perdio entre otros. Sigo muy interesado en [puesto / practicas en seguridad] en
[empresa].

Si el proceso esta cerrado o no es el momento, tambien me sirve saberlo.

Gracias,
{CANDIDATO['nombre']}

---

## Lo que NO hay que hacer

- Mandar el mismo correo a 50 empresas con copia oculta. Se nota y se borra.
- Empezar con "Espero que se encuentre bien". Gasta la primera linea, que es
  la unica garantizada.
- Adjuntar el CV sin nombrarlo bien. Usa
  `Nombre-Apellido-CV-Ciberseguridad.pdf`, no `CV final v3.pdf`.
- Pedir "cualquier oportunidad". Pide una cosa concreta.
""",
        ["[[guias/plan-de-accion-30-dias]]", "[[perfil/fortalezas-diferenciadoras]]",
         "[[guias/empresas-objetivo-en-monterrey]]", "[[01-wiki]]"],
        "Guias de accion", "Correos de postulacion",
    )


# ---------------------------------------------------------------------------

def _linkedin_github() -> None:
    nota(
        "guias/optimizar-linkedin-y-github",
        "Optimizar LinkedIn y GitHub",
        "guia", "pendiente",
        ctx("como dejar los dos perfiles que un reclutador va a abrir")
        + f"""
## Por que importa mas de lo que parece

Un reclutador tecnico hace tres cosas: lee el titular de LinkedIn, abre el
GitHub y decide. Si el GitHub no respalda lo que promete el CV, la credibilidad
se cae justo en el momento en que mas la necesitas.

## LinkedIn

**Titular.** El titular es un campo de busqueda: los reclutadores filtran por
esas palabras. Debe contener los terminos por los que quieres que te encuentren.

> [Tu perfil] · [tus dos o tres areas fuertes] ·
> [lo que te diferencia] · Busco [lo que buscas]

**Acerca de.** Tres parrafos cortos: que has construido (con numeros), que te
diferencia (tu cruce de areas, si lo tienes) y que buscas (tipo de puesto y
zona). Nada de frases de motivacion genericas.

**Experiencia.** Cada punto empieza con un verbo y termina en un numero:
"Ejecute la auditoria interna: N hallazgos mapeados al Anexo A de ISO 27001".

**Activar "Open to work".** Solo visible para reclutadores, con los puestos
"Analista de ciberseguridad", "Analista SOC", "Practicante de TI",
"GRC Analyst". Los reclutadores filtran por esa senal.

**Idioma.** Perfil en espanol, pero con los terminos tecnicos en ingles
(ISO 27001, SIEM, incident response). Asi apareces en las dos busquedas.

## GitHub — {CANDIDATO['github']}

**El README del perfil es tu portada.** Crea un repositorio con tu mismo
nombre de usuario y escribe ahi quien eres en cinco lineas.

**Tu mejor proyecto necesita un README de verdad.** Casi siempre el proyecto es
mas interesante de lo que se puede ver desde fuera. Deberia contener:

1. Un parrafo que un no experto entienda: que hace y por que es dificil.
2. El detalle tecnico: que hace cada pieza.
3. **Los numeros**: la metrica antes y despues, el tamano del banco de pruebas.
   Es lo que separa "hice un proyecto" de "medi si funcionaba".
4. Una captura o un GIF. Un lector le da 30 segundos; una imagen los gana.
5. Como ejecutarlo.

**Fija los repositorios buenos arriba** (pinned) y archiva los de practica.
Un GitHub con 3 repositorios buenos vende mas que uno con 20 tibios.

## Lo que convierte esto en entrevistas

Cuando escribas el correo de [[guias/correos-de-postulacion]], el enlace a
GitHub deja de ser decorativo: es la prueba de lo que afirmas en la primera
linea. Por eso este trabajo va **antes** de la ronda de postulaciones.
""",
        ["[[perfil/brechas-y-como-cerrarlas]]", "[[guias/correos-de-postulacion]]", "[[01-wiki]]"],
        "Guias de accion", "Optimizar LinkedIn y GitHub",
    )


# ---------------------------------------------------------------------------

def _entrevista_ingles() -> None:
    nota(
        "guias/entrevista-tecnica-en-ingles",
        "Entrevista tecnica en ingles",
        "guia", "pendiente",
        ctx("como pasar de un ingles intermedio a defender una entrevista tecnica")
        + """
## El diagnostico correcto

El problema no es tu nivel de ingles general. Es que nunca has narrado TU
trabajo en ingles. Son dos habilidades distintas, y la segunda se entrena en
semanas, no en anios.

## El metodo: guiones, no gramatica

Prepara y memoriza el arranque de tres historias. Solo el arranque: una vez que
empiezas, el resto sale.

Las tres de abajo son EJEMPLOS DE FORMATO, no logros de nadie: fijate en la
estructura (que hiciste, con que alcance, con que resultado medible) y
escribelas con lo tuyo, que sale de `perfil.LOGROS`.

**Historia 1 — Un proyecto de implantacion**
> "In my last internship I built [what you built] from scratch, aligned to
> [the standard]. That meant [N] deliverables: [list the kinds]."

**Historia 2 — Una revision o auditoria**
> "After building it, I ran [the review]. I documented [N] findings, classified
> them by severity with technical evidence, and turned them into a prioritized
> remediation plan."

**Historia 3 — Un proyecto propio**
> "On my own time I built [the tool]. It has [the mechanism], and [the way you
> measured it], so I can tell whether a change actually improved things or just
> felt better."

## Vocabulario que si vas a necesitar

| Espanol | Ingles |
|---|---|
| matriz de riesgos | risk matrix / risk register |
| hallazgo de auditoria | audit finding |
| plan de remediacion | remediation plan |
| respuesta a incidentes | incident response |
| endurecimiento | hardening |
| cuentas privilegiadas | privileged accounts |
| minimo privilegio | least privilege |
| segregacion de funciones | segregation of duties |
| concientizacion | security awareness |
| controles compensatorios | compensating controls |

## Practica diaria: 20 minutos

1. Elige una historia y cuentala en voz alta, grabandote.
2. Escuchate. Anota solo donde te trabaste.
3. Repitela arreglando ese punto.

No estudies gramatica. Repite hasta que las tres historias salgan solas.

## Frases para sobrevivir a un tropiezo

- "Let me rephrase that." — cuando te enredas.
- "Could you repeat the question, please?" — sin disculparte.
- "I haven't worked with that specific tool, but I've done something similar
  with..." — la mejor respuesta a algo que no sabes.

## Lo que NO debes hacer

Poner "ingles avanzado" en el CV si no lo es. Si te llaman y no lo sostienes,
pierdes la vacante y la credibilidad. Declara tu nivel real con su etiqueta
--el que tengas en `perfil.CANDIDATO`-- y anade que sabes leer documentacion
tecnica si es cierto: eso es honesto y suficiente para la mayoria de puestos
remotos de LatAm.
""",
        ["[[perfil/brechas-y-como-cerrarlas]]", "[[guias/plan-de-accion-30-dias]]", "[[01-wiki]]"],
        "Guias de accion", "Entrevista tecnica en ingles",
    )


# ---------------------------------------------------------------------------

def _empresas_objetivo(vacantes: list[dict]) -> None:
    amm = [
        v for v in vacantes
        if any(m in v.get("ubicacion", "").lower()
               for m in ("monterrey", "nuevo le", "apodaca", "san pedro",
                         "guadalupe", "santa catarina", "escobedo", "garcía", "garcia"))
    ]
    empresas: dict[str, list[dict]] = {}
    for v in amm:
        empresas.setdefault(v["empresa"], []).append(v)
    ordenadas = sorted(
        empresas.items(),
        key=lambda kv: -max(x["score"] for x in kv[1]),
    )[:30]

    filas = []
    for emp, vs in ordenadas:
        mejor = max(vs, key=lambda x: x["score"])
        filas.append(
            f"- [[vacantes/{_slug_vac(mejor)}|{emp} — {mejor['titulo'][:52]}]] "
            f"({mejor['score']:.0f}/100)"
            if mejor.get("_nota_creada")
            else f"- **{emp}** — {mejor['titulo'][:60]} ({mejor['score']:.0f}/100)"
        )

    nota(
        "guias/empresas-objetivo-en-monterrey",
        "Empresas objetivo en Monterrey",
        "guia", "en-progreso",
        ctx("a que empresas de Monterrey conviene escribir, con y sin vacante publicada")
        + f"""
## Empresas con vacante detectada en el area metropolitana

Estas salieron de la ultima corrida del sistema y estan en el panel
([[sistema/panel-de-vacantes]]) con su enlace para postular.

{chr(10).join(filas) if filas else '[COMPLETAR: ejecutar el pipeline para poblar esta lista]'}

## Empresas para candidatura espontanea

Estas **no tienen vacante de practicas detectada ahora mismo**. Se listan
porque tienen operacion de TI o seguridad en Monterrey y son destinos logicos
para el correo de la plantilla 3 de [[guias/correos-de-postulacion]]. No son
vacantes: son objetivos de contacto.

**Corporativos regiomontanos con area de TI grande**
- Banorte (sede en Monterrey; area de seguridad de la informacion propia)
- FEMSA / Coca-Cola FEMSA / OXXO
- CEMEX
- Ternium
- Alfa, Sigma, Nemak
- Arca Continental
- Grupo Axtel (telecomunicaciones; opera un SOC)
- Banregio
- Deacero, Xignux, Katcon, Metalsa, Frisa
- Vitro

**Consultoras y servicios de TI con oficina en Monterrey**
- Softtek (origen regiomontano; contrata practicantes)
- Neoris
- Accenture Mexico
- Deloitte, PwC, KPMG, EY — sus areas de Risk Advisory y Cyber
- Capgemini Mexico
- Axity
- Monterrey IT Cluster — asociacion que agrupa a muchas de estas

**Empresas especializadas en ciberseguridad en Mexico**
- Smartekh
- Scitum (grupo Telmex; opera uno de los SOC mas grandes del pais)
- Ikusi
- bSide
- Overclockers Mexico
- Gestion de Tecnologia Especializada

**La via mas corta y la mas ignorada**
- La coordinacion de tu carrera. Las facultades tienen convenios
  de practicas que nunca se publican en bolsas de trabajo.
- La bolsa de trabajo institucional de tu universidad.
- El Monterrey IT Cluster: preguntar por su programa de talento.

## Como usar esta lista

Para cada empresa: buscar en LinkedIn "[empresa] seguridad informacion" o
"[empresa] CISO", encontrar una persona real, y mandar la plantilla 3. Cinco
correos bien dirigidos por semana rinden mas que cincuenta formularios.
""",
        ["[[guias/correos-de-postulacion]]", "[[sistema/panel-de-vacantes]]",
         "[[guias/plan-de-accion-30-dias]]", "[[01-wiki]]"],
        "Guias de accion", "Empresas objetivo en Monterrey",
    )


def _slug_vac(v: dict) -> str:
    from generar_obsidian import kebab
    return f"{kebab(v['empresa'])}-{kebab(v['titulo'])}"[:70]


# ---------------------------------------------------------------------------

def _como_usar_el_sistema(est: dict) -> None:
    # Contra la base, nunca contra `est`: `est["vivas"]` es el recuento de
    # una corrida y publicaba 2.228 donde el panel ensenaba 3.700.
    _c = cifras_panel()
    _u = ultima_corrida()
    nota(
        "guias/como-usar-el-sistema",
        "Como usar el sistema",
        "guia", "hecho",
        ctx("las instrucciones de operacion diaria del sistema")
        + f"""
## Rutina recomendada

**Cada lunes**, dos comandos:

```bash
python app/pipeline.py
python app/generar_dashboard.py
```

El primero recolecta, deduplica, puntua y verifica. El segundo reconstruye
`dashboard.html`. Tus vacantes marcadas como aplicadas NO se pierden: viven en
el navegador, no en el archivo.

**Para regenerar tambien las notas de esta boveda:**

```bash
python app/generar_todo.py
```

## Que hacer con cada veredicto

| Veredicto | Que significa | Accion |
|---|---|---|
| `aplicar-ya` | 72+ puntos: nivel, area y geografia encajan | Postular esta semana, con correo directo |
| `buen-fit` | 56-71: encaja pero con alguna friccion | Postular si tienes hueco |
| `explorar` | 40-55: adyacente | Leer la descripcion antes de invertir tiempo |

## Que significa cada estado de verificacion

- **viva** — confirmada abierta. Verde para postular.
- **sin verificar** — exige sesion iniciada o la pagina no dio senal clara.
  Abrela y comprueba tu mismo antes de invertir tiempo en la carta.
- **inaccesible** — la pagina no respondio. Reintentar mas tarde.

## Ajustar el sistema a tu criterio

- **Cambiar que habilidades pesan:** `app/perfil.py`, diccionario `HABILIDADES`.
- **Anadir una empresa a vigilar:** `app/fuentes_ats.py`, listas por ATS.
- **Cambiar los umbrales de veredicto:** `app/analisis.py`, lista `VEREDICTOS`.
- **Anadir busquedas de Mexico:** `app/fuentes_mexico.py`, lista `CONSULTAS_MX`.

Despues de tocar cualquier cosa del clasificador, ejecuta las pruebas:

```bash
python app/test_analisis.py
```

Estan ahi porque dos errores reales de clasificacion se colaron hasta el
dashboard antes de detectarse. Ver [[sistema/clasificador-y-scoring]].

## Estado actual

- Vacantes vivas en el panel: **{_c['panel']}**
- En el historial completo: **{_c['historicas']}**
- Ultima corrida: **{_u['guardadas']}** guardadas, **{_u['nuevas']}** nuevas ({_u['inicio'][:10]})
""",
        ["[[sistema/panel-de-vacantes]]", "[[sistema/clasificador-y-scoring]]", "[[01-wiki]]"],
        "Guias de accion", "Como usar el sistema",
    )

    nota(
        "guias/sincronizar-con-notebooklm",
        "Sincronizar las vacantes con NotebookLM",
        "guia", "en-progreso",
        ctx("como hacer que NotebookLM se entere solo de las vacantes nuevas")
        + """
## Por que hace falta un rodeo

NotebookLM **no tiene API publica**: no se le puede subir nada por programa.
Pero desde el 26 de mayo de 2026 mantiene una conexion viva con Google Drive:
si una fuente del cuaderno es un documento **nativo** de Workspace, la relee
sola cada pocos minutos.

Entonces el camino es indirecto pero automatico:

```
excavadora  ->  exportar_corpus  ->  sincronizar_drive (actualiza el Doc)
                                 ->  NotebookLM lo absorbe solo
```

**Aviso que cuesta caro ignorar:** un `.txt` subido a Drive NO se sincroniza
nunca. Tiene que ser Google Doc nativo. Por eso `sincronizar_drive.py` sube el
texto pidiendo la conversion a `application/vnd.google-apps.document`.

## Alta de credenciales (una sola vez)

1. Entrar en <https://console.cloud.google.com/> y crear un proyecto nuevo.
2. **APIs y servicios -> Biblioteca**: buscar *Google Drive API* y habilitarla.
3. **Pantalla de consentimiento OAuth**: tipo **Externo**, poner un nombre y el
   correo propio. Anadirse a uno mismo como **usuario de prueba**.
4. **Credenciales -> Crear credenciales -> ID de cliente de OAuth**, tipo
   **Aplicacion de escritorio**. Descargar el JSON.
5. Guardarlo como `app/datos/credenciales_drive.json`.

La primera ejecucion abre el navegador para autorizar y deja el permiso
guardado en `app/datos/token_drive.json`. No hay que repetirlo.

## Permisos: solo lo minimo

Se pide el alcance `drive.file`, que da acceso **unicamente a los archivos que
crea este propio programa**. No puede leer ni modificar el resto del Drive
aunque hubiera un fallo en el codigo.

## Uso

```bash
python app/sincronizar_drive.py            # regenera el corpus y lo sube
python app/sincronizar_drive.py --estado   # que documentos existen ya
python app/sincronizar_drive.py --minimo 10  # solo si hay 10+ vacantes nuevas
```

La excavadora lo llama sola al terminar, con `minimo_nuevas=5`, y **nunca
falla la corrida por esto**: si no hay credenciales, lo salta y sigue.

## Detalles que evitan romper el cuaderno

- **Se reemplaza el contenido, no se crea otro documento.** El identificador
  del Doc se guarda en `app/datos/drive_documentos.json`. Si se creara uno
  nuevo en cada corrida, el cuaderno seguiria leyendo el viejo para siempre.
- **Se corta entre vacantes.** Un Google Doc admite algo mas de un millon de
  caracteres y el corpus de TI general pasa de 2,6 millones, asi que se parte
  en trozos de 900.000. El corte cae siempre en el limite de una ficha: una
  vacante partida en dos documentos daria citas sin sentido.
- Comprobado sobre el corpus real: 1.266 fichas antes de partir, 1.266
  despues, repartidas en 6 documentos.

## Que NO se sincroniza

Solo se suben los archivos de vacantes (`01-`, `02-`, `03-`). La boveda, el
codigo y el perfil se subieron una vez a mano: cambian solo cuando alguien los
edita, y no tiene sentido reescribir 850 KB en Drive en cada corrida.
""",
        ["[[sistema/corpus-para-notebooklm]]", "[[guias/como-usar-el-sistema]]", "[[01-wiki]]"],
        "Guias de accion", "Sincronizar con NotebookLM",
    )


# ---------------------------------------------------------------------------

def _cuanto_ahorra_la_boveda() -> None:
    """La nota del experimento del 27-ago-2026, ya pasada por el jefe.

    Las cifras van escritas a mano A PROPOSITO: son el resultado de una
    medicion fechada, no el estado de hoy. Meterlas por `est` seria repetir el
    fallo que este mismo experimento destapo.

    Segunda version. La primera afirmaba un 42% de ahorro, un ratio de 1,4
    caracteres por token y una "comprobacion independiente" con un 5% de error.
    El jefe tumbo las tres: el 42% no devolvia un archivo leido fuera de la
    ventana, el 1,4 salia de elegir la calibracion que encajaba entre dos que
    discrepaban un 31%, y la comprobacion era circular. Queda el 51% de
    material leido, que no depende de ninguna de esas cosas.
    """
    nota(
        "sistema/cuanto-ahorra-la-boveda",
        "Cuanto ahorra la boveda, medido",
        "decision", "hecho",
        ctx("el experimento que midio si la boveda ahorra tokens de verdad, "
            "en cuanto, y en que casos no")
        + """
## Por que existe esta nota

La boveda se defendia con un argumento sin numeros: "asi el agente no tiene que
leerse el codigo". El 27-ago-2026 se midio, porque un ahorro supuesto es una
decision de diseno sin comprobar.

## Como se midio

Dos sesiones de Claude Code respondieron **las mismas tres preguntas**, a la vez
y sin verse:

1. Por que el ATS es la fuente primaria y que NO se tomo del software libre.
2. Como se decide que una vacante sigue viva, y que respuesta HTTP la cierra.
3. Cuantas vacantes hay en el panel y cuantas candidaturas enviadas.

Un brazo con la boveda **prohibida** (solo `app/`, la base y el panel); el otro
navegando por enlaces desde `00-INICIO`, como manda [[reglas-de-la-boveda]]. El
coste se leyo del `usage` real que Claude Code guarda por turno, con
una herramienta de medicion propia, la misma en los dos brazos.

## Resultado

| | Sin boveda | Con boveda |
|---|---|---|
| **Material bruto leido** | 28.776 caracteres | **14.235 caracteres** |
| Tokens nuevos en la ventana | 18.246 | **12.100** |
| Turnos | 16 | **4** |

**La cifra buena es la primera: 51% menos material leido.** Es un conteo de
caracteres de los archivos que cada brazo abrio, y no depende ni de la densidad
de tokens ni de donde se corte la ventana de medicion.

La de tokens (34% menos) es mas debil y conviene saber por que: `tokens_nuevos`
incluye tambien el texto que escribe el propio agente y su pensamiento, y eso se
paga **por turno**. Con 16 turnos frente a 4, una parte del hueco es el agente
escribiendo mas, no leyendo mas.

## De donde sale el ahorro

No de leer menos lineas: de **no buscar**. El brazo sin boveda gasto dos `grep`
a ciegas —el primero devolvio 20 archivos por el ruido de "open source" en
`dominio.py`— y tres turnos localizando el `WHERE` del panel dentro de
`servidor.py`. El brazo con boveda no busco: `00-INICIO` le dijo a que nota ir y
`estado-actual` ya traia el filtro escrito.

## Por que no se lee entera

| Leer... | Caracteres | Tokens aprox. |
|---|---|---|
| El camino navegado | 14.112 | ~7.000 |
| La boveda entera (106 notas) | 362.683 | ~181.000 |
| Todo `app/*.py` | 861.839 | *no medido* |

A **~2,0 caracteres por token** (medido en tres muestras de markdown en espanol:
1,95 · 1,95 · 2,15), leerla entera cuesta **25,7 veces** el camino navegado —y
ese cociente es de caracteres, asi que no depende del ratio. La linea de
`app/*.py` se deja sin convertir a proposito: la densidad de Python no se midio,
y este proyecto ya publico bastantes numeros sin respaldo por un dia.

`vacantes/` es mas de la mitad de la boveda siendo datos: su sitio es el panel.

## Donde la boveda PIERDE

**En las cifras, y ese dia perdio feo.** Cinco notas publicaban 2.228 vacantes
vivas, `estado-actual` decia 3.691 y la base 3.700, todo el mismo dia. No era
una causa sino tres: cuatro notas leian `estadisticas.json` (un derivado), una
tenia el numero **escrito a mano** en el generador, y otra llamaba "historial" a
lo que no lo era. El 2.228 resulto ser `corridas.guardadas` —lo que guardo la
ultima corrida— publicado bajo el nombre `vivas`. Dos cosas distintas con el
mismo nombre: por eso nadie lo vio.

Arreglado con `almacen.cifras_panel()`, que deja el `WHERE` del panel en un solo
sitio. Pero el arreglo tardo dos intentos, y el segundo es la leccion de verdad:
dimos la boveda por limpia y **nadie miro `generar_dashboard.py`**. El primer
recuadro que abre el usuario seguia diciendo 2.228, volcado de
`estadisticas.json`, y encima el JSON entero viajaba incrustado en el HTML.

**La cicatriz numero uno no vive en un archivo: vive en la costumbre de leer un
derivado.** Buscarla solo donde ya la encontraste es como llega a su cuarta
aparicion. El sitio que nadie revisa es justo el que el usuario abre primero.

**En el detalle fino, y eso no se arregla.** El brazo sin boveda respondio cosas
que la boveda no sabe: que la clave de la app de Indeed es compartida con todos
los usuarios de JobSpy y por eso el ritmo es conservador, o el desglose de
401/403/429 frente a 404/410. El codigo siempre tendra mas detalle que su
resumen. Parte de esos 18.246 tokens compro respuesta que el otro brazo no dio:
no es "lo mismo, mas barato".

## El patron que aparecio tres veces el mismo dia

Las tres cosas que fallaron el 27-ago no son tres fallos distintos: son el mismo.

1. **El 2.228**: cuatro notas publicaban una cifra de un derivado porque encajaba
   con lo que se esperaba ver. Nadie la contrasto con la base.
2. **La pregunta 2 de este experimento**: los dos brazos contestaron como
   funciona el verificador. Ninguno miro si los datos lo cumplian — y no lo
   cumplian: 804 vacantes marcadas `viva` no aparecieron en la corrida de ese
   dia.
3. **La llamada de Red Ambiental**: dos sesiones dieron por hecho que la empresa
   respondia a su candidatura. Era plausible y resulto cierto, pero se supo
   **preguntando al usuario**, no comprobando.

En los tres casos el error no fue de calculo: fue aceptar lo que encajaba sin
que constara. **Encajar no es constar.** Y de los tres, dos los cazo una revision
escrita para desconfiar; ninguno se cazo solo.

## La regla que sale de aqui

- **El porque y el mapa: la boveda.** Decisiones, cicatrices, donde vive cada
  cosa. Ahi ahorra la mitad del material y evita la busqueda a ciegas.
- **Las cifras: SQL**, siempre, via `almacen.cifras_panel()`. Una cifra en la
  boveda es una foto del momento en que se genero.
- **El detalle de implementacion: el codigo**, pero ya sabiendo que archivo
  abrir. Eso es lo que la boveda regala.

## Limites, para no repetir el error de creerselo

- **n = 1**: un juego de tres preguntas, dos sesiones, un dia.
- **Las dos respuestas correctas podian estar igual de obsoletas.** La pregunta
  2 se contesto con el diseno del verificador, y ese mismo dia se descubrio que
  `ver_estado = 'viva'` no caduca: 804 vacantes marcadas vivas no aparecieron en
  la corrida de hoy. Ni la boveda ni el codigo lo decian, porque ninguno de los
  dos mira los datos. La tercera fuente —SQL— era la unica que podia.
- **Ninguna de las dos sesiones empezo en frio.** Traian 43.622 y 101.615 tokens
  de contexto previo. El contexto previo no infla `tokens_nuevos` (ya esta
  cacheado), pero la que uso la boveda conocia el terreno.
- **Los dos brazos no respondieron exactamente lo mismo** (ver arriba). Es el
  sesgo mas gordo y el unico que no se pudo cuantificar.
- **`00-INICIO` se leyo antes de abrir la ventana de medicion** y se devolvio a
  mano al total; sin devolverlo el ahorro parecia del 42%.
- La herramienta de medicion NO forma parte de esta copia, asi que la
  medicion no se puede repetir tal cual desde aqui. Se conserva el dato por
  su valor documental, no como algo reproducible.
""",
        ["[[reglas-de-la-boveda]]", "[[00-INICIO]]", "[[01-wiki]]",
         "[[sistema/corpus-para-notebooklm]]"],
        "Decisiones de diseño", "Cuanto ahorra la boveda, medido",
    )

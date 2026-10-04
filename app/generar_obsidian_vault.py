"""
Notas de vacantes, notas de navegacion y verificacion final de la boveda.

La verificacion de huerfanas al final no es decorativa: es la unica forma de
garantizar mecanicamente la regla "ninguna nota existe si la Wiki no la
enlaza". Si falla, el generador aborta en vez de entregar una boveda rota.
"""
from __future__ import annotations

import re
from pathlib import Path

import generar_obsidian as go
from almacen import cifras_panel
from generar_obsidian import VAULT, ctx, kebab, nota
from nucleo import log
from perfil import CANDIDATO

RUTA_CODIGO = str(Path(__file__).resolve().parent)

# Cuantas vacantes reciben nota propia en la boveda. El dashboard muestra
# TODAS; Obsidian guarda las accionables, que son las que se trabajan a mano.
TOPE_NOTAS_VACANTE = 60


# =============================================================== VACANTES ====

def limpiar_vacantes_obsoletas() -> int:
    """Borra las notas de vacantes de corridas anteriores.

    Sin esto, una vacante que sale del top 60 deja su nota en disco pero la
    Wiki deja de enlazarla: queda huérfana y la bóveda incumple su propia
    regla. Se respetan las notas escritas a mano con el prefijo `mi-`.
    """
    carpeta = VAULT / "vacantes"
    if not carpeta.exists():
        return 0
    borradas = 0
    for p in carpeta.glob("*.md"):
        if p.name.startswith("mi-"):
            continue
        p.unlink()
        borradas += 1
    return borradas


def notas_vacantes(vacantes: list[dict]) -> int:
    limpiar_vacantes_obsoletas()
    candidatas = [
        v for v in vacantes if v["veredicto"] in ("aplicar-ya", "buen-fit")
    ]
    candidatas.sort(key=lambda v: -v["score"])
    candidatas = candidatas[:TOPE_NOTAS_VACANTE]

    for v in candidatas:
        slug = f"{kebab(v['empresa'])}-{kebab(v['titulo'])}"[:70]
        ver = v.get("verificacion", {})
        estado_nota = "pendiente"  # ninguna esta postulada todavia

        en_mty = any(
            m in v.get("ubicacion", "").lower()
            for m in ("monterrey", "nuevo le", "apodaca", "san pedro",
                      "guadalupe", "santa catarina", "escobedo")
        )

        motivos = "\n".join(f"- {m}" for m in v.get("motivos", []))
        habs = ", ".join(v.get("habilidades_coincidentes", [])) or "ninguna detectada"
        desc = (v.get("descripcion") or "").strip()[:1800]

        cuerpo = ctx(f"la vacante «{v['titulo']}» en {v['empresa']}") + f"""
## Datos de la vacante

| Campo | Valor |
|---|---|
| Puesto | {v['titulo']} |
| Empresa | {v['empresa']} |
| Ubicacion | {v.get('ubicacion') or 'sin dato'} |
| Modalidad | {v['modalidad']} |
| Nivel | {v['nivel']} |
| Area | {v['area']} |
| Salario | {v.get('salario') or 'no publicado'} |
| Publicada | {v.get('publicado') or 'sin dato'} |
| Fuente | {v.get('fuente', '')} |
| Fit calculado | **{v['score']}/100** ({v['veredicto']}) |

## Enlace para postular

{v['url']}

## Estado de verificacion

- **Estado:** {ver.get('estado') or 'sin-verificar'}
- **Metodo:** {ver.get('metodo') or '-'}
- **Detalle:** {ver.get('detalle') or '-'}
- **Comprobado:** {(ver.get('fecha') or '-')[:16].replace('T', ' ')}

## Por que encaja contigo

{motivos or '- sin motivos registrados'}

**Habilidades de tu CV que aparecen aqui:** {habs}

{'**Presencial en el area de Monterrey: no exige mudanza ni visa.**' if en_mty else ''}
{'**Exige mudarse dentro de Mexico.**' if v.get('requiere_mudanza') else ''}

## Que escribir

Usa la plantilla que corresponda de [[guias/correos-de-postulacion]]:
{'la plantilla 1, en espanol.' if en_mty or v['modalidad'] != 'remoto' else 'la plantilla 2, en ingles, si la vacante esta en ingles.'}

Angulo recomendado segun el area de esta vacante:
{_angulo(v)}

## Seguimiento

- [ ] Postulada por el formulario
- [ ] Correo directo enviado a una persona concreta
- [ ] Seguimiento a los 7 dias
- [ ] Respuesta recibida

## Extracto de la descripcion

> {desc.replace(chr(10), ' ')[:1500] if desc else '[COMPLETAR: abrir el enlace y pegar aqui lo relevante]'}
"""
        nota(
            f"vacantes/{slug}",
            f"{v['empresa']} — {v['titulo']}"[:90],
            "vacante", estado_nota, cuerpo,
            ["[[guias/correos-de-postulacion]]", "[[sistema/panel-de-vacantes]]", "[[01-wiki]]"],
            _categoria(v),
            f"{v['empresa']} — {v['titulo']}"[:80],
        )
    return len(candidatas)


def _ahora_legible() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _situacion() -> dict:
    """Estado real de la busqueda. Si algo falla, devuelve vacio en vez de
    romper la generacion de la boveda: una nota sin cifra es recuperable, una
    boveda que no se genera bloquea el trabajo."""
    try:
        import cola
        return cola.situacion()
    except Exception:
        return {}


def _categoria(v: dict) -> str:
    en_mty = any(
        m in v.get("ubicacion", "").lower()
        for m in ("monterrey", "nuevo le", "apodaca", "san pedro",
                  "guadalupe", "santa catarina", "escobedo")
    )
    if en_mty:
        return "Vacantes en Monterrey"
    if v["modalidad"] == "remoto":
        return "Vacantes remotas"
    return "Vacantes en otras ciudades"


def _angulo(v: dict) -> str:
    """Con que conviene abrir el correo, segun el area de la vacante.

    Dice QUE TIPO de hecho funciona en cada area, no cual es tu hecho: eso sale
    de `perfil.LOGROS`, que lo rellenas tu. Una plantilla que nombrara logros
    concretos estaria poniendo en tu boca los de otra persona.
    """
    if v["area"] == "ciber-ia":
        return ("Abre con tu trabajo de seguridad de IA y con la metrica que usaste "
                "para medirlo. Es el cruce que casi ningun candidato tiene. "
                "Ver perfil.LOGROS['ia'].")
    if v["area"] == "ia":
        return ("Abre con lo que hayas construido en IA o datos y con la metrica "
                "contra la que lo evaluaste, no con la herramienta. "
                "Ver perfil.LOGROS['ia'].")
    if v["area"] == "ciberseguridad":
        return ("Abre con tu entregable de seguridad mas verificable y con sus "
                "numeros: los numeros pasan los filtros y se recuerdan. "
                "Ver perfil.LOGROS['ciberseguridad'].")
    return ("Abre con una automatizacion o un endurecimiento que hayas hecho tu y "
            "que deje evidencia. Ver perfil.LOGROS['ti'].")


# ============================================================ NAVEGACION =====

def notas_navegacion(est: dict | None = None, vacantes: list[dict] | None = None) -> None:
    """Genera 00-INICIO, hoja-de-producto, plantilla, guia y reglas.

    `est` no alimenta cifras desde el 27-ago-2026: todas salen de la base por
    `cifras_panel()`. Ver el fallo en `generar_obsidian.notas_sistema`.
    """
    vacantes = vacantes or []
    _cif = cifras_panel()

    nota(
        "hoja-de-producto",
        "Hoja de producto — ULTRA CHAMBA",
        "producto", "hecho",
        f"""Esta nota es la ficha principal del proyecto, parte de [[01-wiki]]. Si eres un agente de IA y solo puedes leer dos notas, lee [[00-INICIO]] y esta.

## Que es

ULTRA CHAMBA es un sistema local de busqueda de empleo para
{CANDIDATO['nombre']}. Recolecta vacantes de las bolsas oficiales de cientos de
empresas y de bolsas publicas, descarta las que no encajan con su perfil,
comprueba que cada una siga abierta, y las presenta ordenadas por que tanto le
convienen.

**El problema que resuelve.** Buscar practicas manualmente significa revisar
decenas de portales, leer cientos de vacantes que no aplican (senior, o
restringidas a otro pais), y perder tiempo postulando a vacantes ya cerradas.
Este sistema hace las tres cosas de forma automatica y deja el criterio
auditable: cada recomendacion viene con sus razones.

## Logo

![[logo.png]]

> Para que el logo se vea: coloca el archivo `logo.png` en la carpeta
> `assets/` de esta boveda y renombra el embed a `![[assets/logo.png]]`.
> [COMPLETAR: no existe todavia un logo del proyecto]

## Codigo fuente

Repositorio: {RUTA_CODIGO}

Es una ruta local, no un repositorio remoto.
[COMPLETAR: si se publica en GitHub, sustituir esta ruta por la URL]

## Stack tecnologico

- **Python 3.12** — todo el motor (recoleccion, clasificacion, verificacion).
- **requests + BeautifulSoup + lxml** — HTTP y lectura de HTML.
- **HTML + CSS + JavaScript sin dependencias** — el panel de vacantes.
- **Obsidian** — esta boveda, como memoria del proyecto.
- **Chrome (extension)** — verificacion de paginas que exigen JavaScript.

## Archivos que produce

| Archivo | Que contiene |
|---|---|
| `dashboard.html` | El panel navegable con todas las vacantes |
| `app/datos/vacantes.json` | Las vacantes vivas y relevantes |
| `app/datos/vacantes_cerradas.json` | Las descartadas por estar cerradas |
| `app/datos/vacantes_todas_analizadas.json` | Todo lo analizado, sin filtrar |
| `app/datos/estadisticas.json` | Metricas de la ultima corrida |

## Estado ahora mismo (contra la base, no contra un JSON)

- Vacantes en juego: **{_cif['en_juego']}**
- Vacantes que lista el panel: **{_cif['panel']}** (incluye
  {_cif['descartadas_a_mano']} ya descartadas a mano, con motivo escrito)
- Historico acumulado: **{_cif['historicas']}** ({_cif['cerradas']} cerradas y archivadas)
- Las que exporta `vacantes.json`: **{_cif['exportables']}**
- **Candidaturas enviadas: {_cif['candidaturas_enviadas']}** — la metrica que manda
- Vacantes distintas que ha tocado: **{_cif['vacantes_con_candidatura']}**
- Vacantes marcadas como postuladas: **{_cif['aplicadas']}** — sale mas alto
  porque incluye republicaciones de la misma vacante, marcadas para que el
  ranking no se las vuelva a ofrecer. Es una senal para el ranking, no una
  cuenta de puertas tocadas: hasta el 27-ago-2026 esta linea publicaba ese
  numero bajo el rotulo "Ya postuladas" y no era ninguna de las dos anteriores.

Estas cifras salian de `datos/estadisticas.json` hasta el 27-ago-2026, y decian
2.228 mientras el panel ensenaba 3.700 el mismo dia. Ese numero era
`corridas.guardadas` de la ultima corrida, no las vacantes vivas: dos cosas
distintas con el mismo nombre. Ver [[sistema/almacen-sqlite]].

## Una nota sobre el esquema de metadatos

El esquema original de tipos era `navegacion | producto | feature | componente
| decision | guia`. Se anadio **`vacante`**. Justificacion desde los tres roles:
la entidad central de esta boveda es la oferta de empleo, y meterla dentro de
`feature` haria que un agente frio la leyera como una funcionalidad del
software en vez de como una oportunidad de trabajo — exactamente el modo de
fallo que las reglas piden evitar. Ver [[reglas-de-la-boveda]].

## Notas hermanas

- [[00-INICIO]] — la puerta de entrada
- [[01-wiki]] — el indice de todo
""",
        ["[[00-INICIO]]", "[[01-wiki]]", "[[reglas-de-la-boveda]]"],
        "Producto", "Hoja de producto",
    )

    nota(
        "plantilla-nota",
        "Plantilla base de nota",
        "guia", "hecho",
        ctx("la plantilla para crear cualquier nota nueva en esta boveda")
        + """
## Como usarla

1. Copia el bloque de abajo a un archivo nuevo.
2. Nombra el archivo en kebab-case, sin acentos ni espacios
   (`analista-soc-banorte.md`, no `Analista SOC Banorte.md`).
3. Colocalo en la carpeta que le corresponda: `sistema/`, `perfil/`,
   `guias/` o `vacantes/`. Nunca crees un tercer nivel de carpetas.
4. **Anade su wikilink a [[01-wiki]] en la categoria correcta.** Este paso no
   es opcional: una nota que la Wiki no enlaza es una nota huerfana, y la regla
   es que no existe.

## Vocabulario cerrado

- `tipo`: `navegacion` | `producto` | `feature` | `componente` | `decision` | `guia` | `vacante`
- `estado`: `hecho` | `en-progreso` | `pendiente`

Ningun valor fuera de estas listas.

## La plantilla

```markdown
---
titulo: Titulo legible de la nota
tipo: vacante
estado: pendiente
fecha-actualizacion: AAAA-MM-DD
relacionado:
  - "[[01-wiki]]"
---

Esta nota documenta X, parte de [[01-wiki]] del proyecto [[hoja-de-producto|ULTRA CHAMBA]].

## Que es

Una o dos frases. Un agente que aterrice aqui sin contexto debe entender de
que se trata sin salir de esta nota.

## Contenido

El cuerpo de la nota. Un tema por nota: si crece demasiado, se divide en dos
y se enlazan entre si.

## Enlaces

- [[01-wiki]]
```

## Por que el frontmatter es identico en todas las notas

Un esquema inconsistente es peor que ninguno: un agente que aprende a leer
`estado` en una nota y no lo encuentra en la siguiente deja de confiar en el
campo y empieza a inferir del texto libre, que es justo donde se equivoca.
""",
        ["[[01-wiki]]", "[[guia-de-migracion]]", "[[reglas-de-la-boveda]]"],
        "Producto", "Plantilla base de nota",
    )

    nota(
        "guia-de-migracion",
        "Guia de migracion de la boveda",
        "guia", "hecho",
        ctx("como se construyo esta boveda y como validarla")
        + """
## Pasos, en orden

1. **Crear la boveda.** La carpeta raiz es la del propio proyecto: la que
   contiene `app/`. Abrirla en Obsidian con "Open folder as vault".

2. **Crear las cuatro carpetas de contenido.** `sistema/`, `perfil/`,
   `guias/`, `vacantes/`, mas `assets/` para imagenes. Ni una mas, y ningun
   nivel adicional dentro de ellas.

3. **Crear [[00-INICIO]].** Es la puerta unica. Dicta el orden de lectura.

4. **Crear [[hoja-de-producto]].** Con la seccion `## Codigo fuente` en el
   formato exacto `Repositorio: <ruta>`, para que un agente la extraiga sin
   interpretar nada.

5. **Crear las notas de contenido**, cada una con el frontmatter de
   [[plantilla-nota]].

6. **Poblar [[01-wiki]] al final**, cuando ya existe todo lo que debe
   enlazar. La Wiki solo lleva encabezados de categoria y wikilinks.

7. **Colocar el logo** en `assets/logo.png` y ajustar el embed de la hoja de
   producto.

8. **Ejecutar la prueba del agente frio** (abajo).

## La prueba del agente frio

Leyendo solo [[00-INICIO]] y [[01-wiki]], comprueba que llegas en un clic a:

- [ ] **Que es este proyecto** → [[hoja-de-producto]]
- [ ] **Donde esta el codigo fuente** → [[hoja-de-producto#Codigo fuente]]
- [ ] **Cualquier cosa ya creada** → cada componente, guia y vacante tiene su
      enlace propio en la Wiki

Si algo exige mas de un clic o hay que adivinar, la boveda falla y hay que
corregir la Wiki, no la nota.

## Como se regenera

Esta boveda la escribe el propio sistema:

```bash
python app/generar_todo.py
```

Ese comando reescribe las notas de sistema, perfil, guias y vacantes, y
reconstruye la Wiki desde cero con el 100% de las notas generadas. Por
construccion no puede dejar huerfanas: una nota solo se escribe pasando por la
funcion que la registra en el indice de la Wiki.

**Cuidado:** las notas que escribas tu a mano en esas carpetas se
sobrescriben si coinciden en nombre de archivo. Para notas propias, usa un
prefijo `mi-` que el generador nunca produce.
""",
        ["[[00-INICIO]]", "[[01-wiki]]", "[[plantilla-nota]]"],
        "Producto", "Guia de migracion",
    )

    _nota_estado(est)
    _nota_reglas()
    _nota_inicio(est, vacantes)


def _nota_estado(est: dict) -> None:
    """Una sola nota con el estado real, para no tener que deducirlo leyendo."""
    from nucleo import cargar_json
    vacantes = cargar_json("vacantes.json", []) or []
    from collections import Counter
    ver = Counter(v.get("verificacion", {}).get("estado") for v in vacantes)
    vere = Counter(v.get("veredicto") for v in vacantes)
    amm = sum(1 for v in vacantes
              if any(m in (v.get("ubicacion") or "").lower()
                     for m in ("monterrey", "nuevo le", "apodaca", "san pedro",
                               "guadalupe", "santa catarina", "escobedo")))
    mudanza = sum(1 for v in vacantes if v.get("requiere_mudanza"))
    practicas = sum(1 for v in vacantes if v.get("nivel") == "practicas")

    nota(
        "estado-actual",
        "Estado actual del proyecto",
        "producto", "en-progreso",
        f"""Esta nota documenta el estado del sistema en su ultima corrida, parte de [[01-wiki]]. Si eres un agente que acaba de llegar, leela despues de [[00-INICIO]]: te evita deducir el estado leyendo el resto.

## Cifras de la ultima corrida

"En el panel" = puntuacion >= 40, elegible desde Mexico, area distinta de
'fuera', nivel no excluido y no verificada como cerrada.

| Dato | Valor |
|---|---|
| Vacantes en el panel | **{len(vacantes)}** |
| Verificadas vivas | {ver.get('viva', 0)} |
| Sin verificar | {ver.get('sin-verificar', 0)} |
| Aplicar ya | {vere.get('aplicar-ya', 0)} |
| Buen fit | {vere.get('buen-fit', 0)} |
| En el area de Monterrey | {amm} |
| Exigen mudarse | {mudanza} |
| De practicas | {practicas} |
| Generado | {_ahora_legible()} |

## LA CIFRA QUE MANDA

| Dato | Valor |
|---|---|
| **Candidaturas ENVIADAS** | **{_situacion().get('enviadas') or 0}** |
| Con respuesta | {_situacion().get('con_respuesta') or 0} |
| Borradores en la cola | {_situacion().get('borradores') or 0} |

Las cifras de arriba son de inventario: dicen cuanto hay, no cuanto se ha
hecho. El sistema llego a recomendar 2.681 vacantes con **cero** postuladas,
y por eso existe [[sistema/cola-de-candidaturas]]. Si esta tabla marca 0,
esa es la unica tarea que importa hoy.

## Que funciona

- Recoleccion concurrente de decenas de miles de URLs — [[sistema/excavadora]]
- Historial persistente que detecta nuevas y desaparecidas — [[sistema/almacen-sqlite]]
- Clasificacion contra el CV con motivos auditables — [[sistema/clasificador-y-scoring]]
- Verificacion en varias capas — [[sistema/verificador-de-vacantes]]
- Panel navegable y esta boveda, regenerables con un comando — [[guias/como-usar-el-sistema]]

## Que esta a medias

- **Verificacion de OCC**: {ver.get('sin-verificar', 0)} vacantes sin confirmar. OCC responde 403
  al HTTP directo y corta con 429 tras unas 200 peticiones desde el navegador.
  El trabajo esta encolado y se reanuda solo — [[sistema/trabajos-por-tandas]].
- **Cuatro plataformas sin cubrir**: Workday, SuccessFactors, iCIMS y Oracle,
  que son las de los corporativos grandes de Monterrey —
  [[sistema/decision-que-tomamos-del-software-libre]].
- **Indeed Mexico**: fuente grande todavia sin integrar.
- **Scoring semantico**: evaluado y pospuesto con motivo —
  [[sistema/decision-scoring-por-palabras-vs-semantico]].

## Que NO hay que rehacer

Estas decisiones ya se tomaron con datos y estan documentadas. Antes de
cambiarlas, lee su nota:

- El ATS como fuente primaria — [[sistema/decision-el-ats-como-fuente-primaria]]
- Que se toma del software libre y que no — [[sistema/decision-que-tomamos-del-software-libre]]
- Palabras clave frente a modelos semanticos — [[sistema/decision-scoring-por-palabras-vs-semantico]]

## Errores ya corregidos, con prueba de regresion

Estan en `app/test_analisis.py` y `app/test_modulos.py`. Si tocas el
clasificador, ejecutalos. Cada caso salio de un fallo real:

- 'intern' casaba dentro de 'internal'
- 'bec' casaba dentro de 'becario'
- 'ciber' dejo de casar con 'ciberseguridad' al poner limites de palabra
- La palabra 'global' del texto de marca colaba vacantes de San Francisco
- 'auditoria' sin contexto tecnico colaba contabilidad
""",
        ["[[00-INICIO]]", "[[hoja-de-producto]]", "[[01-wiki]]"],
        "Empezar aqui", "Estado actual del proyecto",
    )


def _nota_reglas() -> None:
    """Enlaza el archivo de reglas que ya existia en la boveda.

    Existe porque `Obisidian rules.md` estaba en la raiz sin que nada lo
    enlazara: era una nota huerfana segun sus propias reglas.
    """
    nota(
        "reglas-de-la-boveda",
        "Reglas de la boveda",
        "guia", "hecho",
        ctx("las reglas de arquitectura que sigue esta boveda")
        + """
## De donde salen

Del documento `Obisidian rules.md`, en la raiz de la boveda. Ese archivo es el
prompt maestro original; esta nota lo resume y lo enlaza para que no quede
huerfano.

## Las reglas innegociables

1. **Maximo 2 niveles de carpetas.** Los agentes se pierden en jerarquias profundas.
2. **Cero notas huerfanas.** Toda nota es alcanzable desde [[01-wiki]].
3. **Punto de entrada unico:** [[00-INICIO]].
4. **Toda nota es autocontenida:** abre con una linea que dice donde esta parada.
5. **Metadatos uniformes** en todas las notas, con vocabulario cerrado.
6. **Nombres en kebab-case**, sin acentos; prefijo numerico solo en navegacion.
7. **Una nota = un tema.**
8. **El estado vive en el frontmatter**, nunca en la Wiki. La Wiki solo navega.

## Regla de arbitraje

Si la estetica de Obsidian choca con la legibilidad para una IA, gana la IA.

## Como las cumple este sistema de forma mecanica

- La funcion `nota()` de `app/generar_obsidian.py` es el unico camino para
  crear una nota, y registra cada una en el indice de la Wiki. No hay forma de
  crear una huerfana.
- `verificar_boveda()` compara al final las notas en disco contra las
  enlazadas por la Wiki y aborta si no coinciden.
- El vocabulario cerrado se valida con `assert` al escribir cada nota.

## Desviacion documentada

Se anadio el tipo `vacante` al vocabulario. La justificacion esta en
[[hoja-de-producto]].

## Documento original

El archivo completo: `Obisidian rules.md` en la raiz de esta boveda.
""",
        ["[[00-INICIO]]", "[[01-wiki]]", "[[guia-de-migracion]]"],
        "Producto", "Reglas de la boveda",
    )


def _nota_inicio(est: dict, vacantes: list[dict] | None = None) -> None:
    inicio = f"""---
titulo: INICIO — puerta de entrada de la boveda
tipo: navegacion
estado: hecho
resumen: Puerta unica de entrada; enruta a cada tarea sin necesidad de leer la boveda entera
fecha-actualizacion: {go.HOY}
relacionado:
  - "[[estado-actual]]"
  - "[[hoja-de-producto]]"
  - "[[01-wiki]]"
---

# INICIO

Puerta unica de entrada. Si eres un agente que acaba de llegar sin contexto,
estas en el lugar correcto.

**No leas la boveda entera. No hace falta y es contraproducente.** Son 92
notas; con tres y los enlaces correctos tienes todo lo necesario.

## Que es esto

**ULTRA CHAMBA**: un sistema local que busca, filtra y verifica vacantes de
practicas en ciberseguridad e inteligencia artificial para
{CANDIDATO['nombre']}, en Monterrey y en remoto. Esta boveda es su memoria.

## Lee solo estas tres, en este orden

1. **Esta nota** — te dice adonde ir.
2. **[[estado-actual]]** — en que punto esta todo ahora mismo: cifras, que
   funciona, que esta a medias y que decisiones NO hay que rehacer.
3. **[[01-wiki]]** — el indice. Cada cosa que existe tiene ahi su enlace.

Con eso ya puedes trabajar. Lo demas se abre solo cuando lo necesites.

## Segun lo que vengas a hacer

| Si necesitas... | Ve directo a |
|---|---|
| Entender el proyecto | [[hoja-de-producto]] |
| Saber como esta todo hoy | [[estado-actual]] |
| Ejecutar la recoleccion | [[sistema/excavadora#Como se ejecuta]] |
| Entender por que se recomienda una vacante | [[sistema/clasificador-y-scoring]] |
| Anadir una fuente nueva | [[sistema/excavadora#Anadir una fuente nueva]] |
| Saber por que algo se decidio asi | [[estado-actual#Que NO hay que rehacer]] |
| Tocar el clasificador sin romperlo | [[estado-actual#Errores ya corregidos, con prueba de regresion]] |
| Postular a algo hoy | [[guias/plan-de-accion-30-dias]] |
| Escribir el correo | [[guias/correos-de-postulacion]] |
| Mejorar el CV | [[guias/mejorar-el-cv]] |
| Conocer al candidato | [[perfil/perfil-del-candidato]] |
| Saber que NO puede aceptar | [[perfil/restricciones-de-busqueda]] |
| Ver todas las vacantes | `dashboard.html`, doble clic |

## Como navegar sin leerlo todo

- **Cada nota lleva un campo `resumen` en su frontmatter.** Puedes saber de
  que trata cualquier nota sin abrirla. Para conocer la boveda entera basta
  con leer las cabeceras.
- **Todo se alcanza desde [[01-wiki]].** Si algo no esta enlazado ahi, no
  existe aqui.
- **En la Wiki, primero va lo que orienta y al final lo que son datos.** Las
  notas de `vacantes/` son datos: no las leas para orientarte. Estan al final
  y su lugar natural es el panel.
- **El estado de cada cosa vive en el frontmatter**, campo `estado`, nunca en
  la Wiki.
- **Maximo dos niveles de carpetas**: raiz, o `sistema/`, `perfil/`, `guias/`,
  `vacantes/`.

## Antes de cambiar nada

Hay decisiones ya tomadas con datos y errores ya corregidos con pruebas. Estan
en [[estado-actual]]. Rehacerlos cuesta tiempo y reintroduce fallos que ya se
pagaron una vez.

## Estado en una linea

**{len(vacantes)}** vacantes en el panel · **{_situacion().get('enviadas') or 0}**
candidaturas enviadas — que es la cifra que manda.
Generado: {_ahora_legible()}

Las cifras completas y su definicion estan en [[estado-actual]].
"""
    (VAULT / "00-INICIO.md").write_text(inicio, encoding="utf-8")
    go._indice.append(("Empezar aqui", "INICIO — puerta de entrada", "00-INICIO"))


# ================================================================= WIKI ======

# Orden deliberado: primero lo que ORIENTA, al final lo que son DATOS.
# Antes las 60 notas de vacantes iban en medio y suponían el 61% de los
# enlaces: un agente que llegaba a orientarse tenía que pasarlas todas de
# largo. Las vacantes siguen enlazadas (la regla de cero huérfanas manda),
# pero después de todo lo que sirve para navegar.
ORDEN_CATEGORIAS = [
    "Empezar aqui",
    "Producto",
    "Sistema",
    "Guias de accion",
    "Perfil",
    "Vacantes en Monterrey",
    "Vacantes remotas",
    "Vacantes en otras ciudades",
]


def escribir_wiki() -> None:
    """La Wiki: solo encabezados de categoria y wikilinks. Nada mas."""
    por_cat: dict[str, list[tuple[str, str]]] = {}
    for cat, titulo, ruta in go._indice:
        por_cat.setdefault(cat, []).append((titulo, ruta))

    lineas = [
        "---",
        "titulo: Wiki del proyecto",
        "tipo: navegacion",
        "estado: hecho",
        "resumen: Indice de toda la boveda; primero lo que orienta, al final las vacantes que son datos",
        f"fecha-actualizacion: {go.HOY}",
        "relacionado:",
        '  - "[[00-INICIO]]"',
        '  - "[[hoja-de-producto]]"',
        "---",
        "",
        "# Wiki",
        "",
        "Indice de navegacion: cada enlace lleva al lugar exacto de cada cosa.",
        "",
    ]

    # Accesos directos a secciones concretas, no solo a notas. Van primero
    # porque resuelven en un clic las preguntas que más se repiten.
    lineas += [
        "## Acceso rapido",
        "",
        "- [[estado-actual|Estado del proyecto ahora mismo]]",
        "- [[hoja-de-producto#Codigo fuente|Codigo]]",
        "- [[hoja-de-producto#Stack tecnologico|Stack tecnologico]]",
        "- [[sistema/panel-de-vacantes#Donde esta|Panel de vacantes]]",
        "- [[sistema/excavadora#Como se ejecuta|Como ejecutar la recoleccion]]",
        "- [[guias/plan-de-accion-30-dias#Semana 1 — Municion|Que hacer esta semana]]",
        "- [[guias/correos-de-postulacion#Plantilla 1 — Practicas de ciberseguridad en Monterrey (espanol)|Correo en espanol]]",
        "- [[guias/correos-de-postulacion#Plantilla 2 — Seguridad de IA (ingles)|Correo en ingles]]",
        "- [[guias/mejorar-el-cv#Como hacerte el diagnostico|Que cambiar en el CV]]",
        "- [[perfil/perfil-del-candidato#Que sabe hacer, con evidencia|Evidencia del CV]]",
        "- [[perfil/restricciones-de-busqueda|Restricciones duras del candidato]]",
        "- [[guias/como-usar-el-sistema#Rutina recomendada|Como regenerar todo]]",
        "",
    ]

    categorias = ORDEN_CATEGORIAS + [
        c for c in sorted(por_cat) if c not in ORDEN_CATEGORIAS
    ]
    for cat in categorias:
        entradas = por_cat.get(cat)
        if not entradas:
            continue
        lineas.append(f"## {cat}")
        lineas.append("")
        for titulo, ruta in sorted(set(entradas), key=lambda x: x[0].lower()):
            titulo_limpio = titulo.replace("|", "-").replace("[", "(").replace("]", ")")
            lineas.append(f"- [[{ruta}|{titulo_limpio}]]")
        lineas.append("")

    (VAULT / "01-wiki.md").write_text("\n".join(lineas), encoding="utf-8")


# ========================================================== VERIFICACION =====

RX_WIKILINK = re.compile(r"\[\[([^\]|#]+)")

# Un `{algo['clave']}` o `{algo.get(...)}` que sobrevive al generador es un
# f-string al que le falto la `f`. No se buscan llaves a secas: la boveda
# tiene bloques de codigo y JSON legitimos con llaves.
RX_PLANTILLA = re.compile("\\{[a-z_]+(?:\\[|\\.get\\()[^}" + chr(10) + "]{0,60}\\}")


def _secciones_vacias(texto: str) -> list[str]:
    """Encabezados `##` sin una sola linea de contenido debajo."""
    lineas = texto.splitlines()
    vacias = []
    for i, linea in enumerate(lineas):
        if not linea.startswith("## "):
            continue
        for siguiente in lineas[i + 1:]:
            s = siguiente.strip()
            if not s:
                continue
            if s.startswith("## ") or s.startswith("# "):
                vacias.append(linea[3:].strip())
            break
        else:
            vacias.append(linea[3:].strip())
    return vacias


def verificar_boveda() -> tuple[bool, list[str]]:
    """Comprueba las reglas duras. Devuelve (todo_ok, problemas)."""
    problemas: list[str] = []

    notas_disco = {
        p.relative_to(VAULT).with_suffix("").as_posix()
        for p in VAULT.rglob("*.md")
        if not {".obsidian", ".claude"} & set(p.parts)
    }
    # El documento de reglas original no lo genera el sistema; se enlaza aparte.
    notas_disco.discard("Obisidian rules")
    notas_disco.discard("CLAUDE")

    wiki = (VAULT / "01-wiki.md").read_text(encoding="utf-8")
    enlazadas = {m.strip() for m in RX_WIKILINK.findall(wiki)}
    enlazadas.discard("00-INICIO")

    huerfanas = notas_disco - enlazadas - {"01-wiki", "00-INICIO"}
    if huerfanas:
        problemas.append(f"notas huerfanas ({len(huerfanas)}): {sorted(huerfanas)[:6]}")

    rotos = [e for e in enlazadas if e not in notas_disco and e not in ("01-wiki",)]
    if rotos:
        problemas.append(f"enlaces rotos en la Wiki ({len(rotos)}): {sorted(rotos)[:6]}")

    for p in VAULT.rglob("*.md"):
        # `.claude/` es configuracion del proyecto (agentes, permisos), no
        # documentacion: no se le aplican las reglas de la boveda.
        if ({".obsidian", ".claude"} & set(p.parts)
                or p.name in ("Obisidian rules.md", "CLAUDE.md")):
            continue
        rel = p.relative_to(VAULT)
        if len(rel.parts) > 2:
            problemas.append(f"profundidad mayor a 2 niveles: {rel.as_posix()}")
        texto = p.read_text(encoding="utf-8")
        if "[[[" in texto:
            problemas.append(f"wikilink mal formado ([[[[) en {rel.as_posix()}")
        if not texto.startswith("---"):
            problemas.append(f"sin frontmatter: {rel.as_posix()}")
            continue
        for campo in ("titulo:", "tipo:", "estado:", "resumen:",
                      "fecha-actualizacion:", "relacionado:"):
            if campo not in texto[:400]:
                problemas.append(f"frontmatter incompleto ({campo}) en {rel.as_posix()}")

    # REGLA 8: nada de plantillas sin rellenar ni secciones vacias.
    #
    # El 27-ago-2026 una nota se publico con el texto literal
    # `{cif['sin_fecha']} de {cif['panel']} vacantes` porque a la cadena le
    # faltaba la `f` del f-string, y esta verificacion dijo "correcta". Es el
    # fallo silencioso de siempre: la nota existe, esta enlazada, tiene su
    # frontmatter... y le esta ensenando codigo Python al lector.
    #
    # Va junto con las secciones vacias, que son el mismo problema visto del
    # otro lado: un encabezado con nada debajo le dice al lector que la
    # respuesta no existe, cuando casi siempre existe y solo falta consultarla.
    #
    # Lo que esta regla NO prohibe, y se probo: las marcas `[COMPLETAR: ...]`.
    # Al anadirlas aqui saltaron cinco notas, y las cinco eran correctas --no
    # hay logo, el proyecto no esta en GitHub, esa comparacion no se ha hecho,
    # esa ficha no se ha abierto--. Son huecos DECLARADOS, que es justo lo
    # contrario de un fallo: la nota dice en voz alta lo que no sabe. El unico
    # `[COMPLETAR` que si era un fallo decia "ejecutar el pipeline para poblar
    # este dato" sobre un dato que la base ya tenia, y se arreglo consultandolo.
    for p in VAULT.rglob("*.md"):
        if ({".obsidian", ".claude"} & set(p.parts)
                or p.name in ("Obisidian rules.md", "CLAUDE.md")):
            continue
        rel = p.relative_to(VAULT).as_posix()
        texto = p.read_text(encoding="utf-8")
        for m in RX_PLANTILLA.finditer(texto):
            problemas.append(f"placeholder sin interpolar en {rel}: {m.group(0)[:44]}")
        for hueco in _secciones_vacias(texto):
            problemas.append(f"seccion vacia en {rel}: ## {hueco}")

    # La Wiki solo puede contener encabezados, wikilinks y la linea de intro.
    for i, linea in enumerate(wiki.splitlines(), 1):
        s = linea.strip()
        if not s or s.startswith("#") or s.startswith("- [[") or s == "---":
            continue
        if i <= 10 or s.startswith("Indice de navegacion"):
            continue
        if ":" in s and i < 12:
            continue
        problemas.append(f"la Wiki tiene contenido que no es enlace (linea {i}): {s[:52]}")

    return (not problemas), problemas


def informe(n_vacantes: int) -> None:
    ok, problemas = verificar_boveda()
    total = len([p for p in VAULT.rglob("*.md") if not {".obsidian", ".claude"} & set(p.parts)])
    log(f"  notas escritas: {total} (incluye {n_vacantes} de vacantes)")
    if ok:
        log("  VERIFICACION DE LA BOVEDA: correcta")
        log("    - cero notas huerfanas")
        log("    - cero enlaces rotos")
        log("    - frontmatter completo en todas")
        log("    - profundidad maxima de 2 niveles")
        log("    - la Wiki contiene solo enlaces y encabezados")
        log("    - cero plantillas sin interpolar y cero secciones vacias")
    else:
        log("  VERIFICACION DE LA BOVEDA: PROBLEMAS")
        for p in problemas[:12]:
            log(f"    - {p}")

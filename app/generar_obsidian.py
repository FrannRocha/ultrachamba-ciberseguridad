"""
Genera la bóveda Obsidian de ULTRA CHAMBA.

Sigue el "PROMPT MAESTRO: Arquitectura de Bóveda Obsidian Optimizada para
Agentes de IA" (ver [[reglas-de-la-boveda]]). Reglas que este generador respeta
de forma mecánica, no por buena voluntad:

  - Máximo 2 niveles de carpetas.
  - Cero notas huérfanas: la Wiki enlaza el 100% de las notas generadas, y esto
    se comprueba al final con `verificar_sin_huerfanas()`.
  - Frontmatter idéntico en todas las notas, con vocabulario cerrado.
  - La Wiki contiene EXCLUSIVAMENTE wikilinks y encabezados de categoría.
  - Nombres de archivo en kebab-case, sin acentos.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from almacen import cifras_panel
from nucleo import cargar_json, log, sin_acentos
from perfil import CANDIDATO, CERTIFICACIONES, LOGROS

VAULT = Path(__file__).resolve().parent.parent
HOY = date.today().isoformat()

# Vocabulario cerrado de `tipo`. Se añade `vacante` al esquema original y se
# justifica en la hoja de producto: la bóveda documenta un sistema CUYA entidad
# principal es la vacante. Forzarla dentro de `feature` haría que un agente
# frío la leyera como parte del software y no como una oportunidad de empleo,
# que es justo el modo de fallo que las reglas piden evitar.
TIPOS = {"navegacion", "producto", "feature", "componente", "decision", "guia", "vacante"}
ESTADOS = {"hecho", "en-progreso", "pendiente"}

_indice: list[tuple[str, str, str]] = []  # (categoria, titulo_enlace, ruta_sin_ext)


def kebab(texto: str) -> str:
    t = sin_acentos(texto).lower()
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return re.sub(r"-+", "-", t).strip("-")[:70] or "sin-titulo"


def nota(
    ruta: str,
    titulo: str,
    tipo: str,
    estado: str,
    cuerpo: str,
    relacionado: list[str],
    categoria_wiki: str,
    titulo_enlace: str | None = None,
    ancla_wiki: str = "",
) -> None:
    """Escribe una nota con frontmatter uniforme y la registra en el índice.

    Registrar aquí — y solo aquí — es lo que garantiza que no haya huérfanas:
    no existe forma de crear una nota sin que entre al índice de la Wiki.
    """
    assert tipo in TIPOS, f"tipo fuera de vocabulario: {tipo}"
    assert estado in ESTADOS, f"estado fuera de vocabulario: {estado}"

    destino = VAULT / f"{ruta}.md"
    destino.parent.mkdir(parents=True, exist_ok=True)

    # `resumen` se extrae de la primera línea del cuerpo, que por convención
    # dice qué documenta la nota. Va en el frontmatter para que un agente pueda
    # saber de qué trata CADA nota leyendo solo las cabeceras, sin abrir 92
    # archivos. Es el propósito entero de la bóveda: guiarse por la Wiki y los
    # metadatos, no leyéndolo todo.
    primera = next((l.strip() for l in cuerpo.strip().splitlines() if l.strip()), "")
    resumen = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", primera)
    resumen = re.sub(r"\[\[([^\]]+)\]\]", r"\1", resumen)
    resumen = resumen.replace("Esta nota documenta ", "").replace('"', "'").strip()
    resumen = re.sub(r",?\s*parte de .*$", "", resumen).strip(" .") or titulo
    resumen = resumen[:150]

    # Se aceptan los enlaces con o sin corchetes; aquí se normalizan a una
    # sola pareja. Sin esto salía `[[[[nota]]]]`, que Obsidian no resuelve.
    limpios = [r.strip().strip("[]").strip() for r in relacionado]
    rel = "\n".join(f'  - "[[{r}]]"' for r in limpios if r) or '  - "[[01-wiki]]"'
    contenido = (
        "---\n"
        f"titulo: {titulo}\n"
        f"tipo: {tipo}\n"
        f"estado: {estado}\n"
        f"resumen: {resumen}\n"
        f"fecha-actualizacion: {HOY}\n"
        "relacionado:\n"
        f"{rel}\n"
        "---\n\n"
        f"{cuerpo.strip()}\n"
    )
    destino.write_text(contenido, encoding="utf-8")
    _indice.append((categoria_wiki, titulo_enlace or titulo, ruta + ancla_wiki))


def ctx(que: str) -> str:
    """Línea de contexto obligatoria: un agente que aterrice aquí sabe dónde está."""
    return f"Esta nota documenta {que}, parte de [[01-wiki]] del proyecto [[hoja-de-producto|ULTRA CHAMBA]].\n"


# ============================================================ NOTAS DEL SISTEMA

def notas_sistema(est: dict | None = None) -> None:
    """`est` ya NO alimenta ninguna cifra; se conserva por compatibilidad.

    EL FALLO (27-ago-2026, la cicatriz nº1 por tercera vez). Estas notas
    imprimian `est['vivas']`, que sale de `datos/estadisticas.json`. Ese
    numero no es "vacantes vivas": es `corridas.guardadas` de la ULTIMA
    corrida --2.228-- mientras el panel ensenaba 3.700 y `estado-actual`,
    que si lee la base, decia 3.691. La boveda se contradecia a si misma el
    mismo dia, y con fecha de hoy, porque el JSON se reescribe en cada
    corrida: parecia fresco y mentia igual. Ahora todo sale de
    `almacen.cifras_panel()`, con el mismo WHERE que usa el panel.
    """
    cif = cifras_panel()
    bolsas = cif["por_ats"]
    total_bolsas = sum(bolsas.values())

    nota(
        "sistema/motor-de-recoleccion",
        "Motor de recoleccion",
        "componente", "hecho",
        ctx("el componente que descarga vacantes de todas las fuentes")
        + f"""
## Que hace

Consulta en paralelo tres familias de fuentes y devuelve todas las vacantes en
un mismo formato normalizado.

## Fuentes que consulta

1. **ATS oficiales** — las bolsas de trabajo de cada empresa. Ver [[sistema/catalogo-de-fuentes]].
2. **Bolsas remotas globales** — RemoteOK, Remotive, Himalayas, Arbeitnow, Jobicy, WeWorkRemotely, WorkingNomads.
3. **Bolsas de Mexico** — OCC Mundial y Computrabajo, que concentran lo presencial de Monterrey.
4. **LinkedIn** — via su API publica de invitado, sin necesidad de iniciar sesion.

## Lo que hay recolectado ahora (contado contra la base)

- Vacantes que ensena el panel: **{cif['panel']}**
- De ATS oficiales: **{total_bolsas}** ({len(bolsas)} bolsas de empresa distintas)
- Historico acumulado, incluido lo ya cerrado: **{cif['historicas']}**

## Codigo

`app/fuentes_ats.py`, `app/fuentes_boards.py`, `app/fuentes_mexico.py`.
Ubicacion completa en [[hoja-de-producto#Codigo fuente]].

## Como se ejecuta

```bash
python app/pipeline.py
```
""",
        ["[[sistema/catalogo-de-fuentes]]", "[[sistema/clasificador-y-scoring]]", "[[01-wiki]]"],
        "Sistema", "Motor de recoleccion",
    )

    filas = "\n".join(
        f"- **{k}**: {v} bolsas de empresa respondiendo" for k, v in bolsas.items() if v
    )
    nota(
        "sistema/catalogo-de-fuentes",
        "Catalogo de fuentes",
        "componente", "hecho",
        ctx("de donde salen las vacantes y por que se confia en cada fuente")
        + f"""
## Jerarquia de confianza

No todas las fuentes valen lo mismo. El sistema las ordena asi:

1. **ATS oficial (maxima confianza).** Greenhouse, Lever, Ashby, SmartRecruiters.
   Son la bolsa de trabajo de la propia empresa. Si el API la devuelve, la
   vacante esta publicada en este momento. Ver [[sistema/decision-el-ats-como-fuente-primaria]].
2. **Bolsa de Mexico y LinkedIn (confianza media).** OCC, Computrabajo y
   LinkedIn. Publican rapido pero tardan en retirar lo cerrado, asi que se
   verifican una por una.
3. **Agregador remoto (confianza baja).** Copian de otras fuentes y se
   desfasan. Utiles para descubrir, obligatorio verificarlos.

## Nota sobre LinkedIn

LinkedIn bloquea su buscador con un muro de sesion, pero expone
`/jobs-guest/jobs/api/seeMoreJobPostings/search` y
`/jobs-guest/jobs/api/jobPosting/{id}`, que devuelven resultados y ficha
completa **sin sesion**. Por eso el sistema incluye LinkedIn sin manejar
credenciales del usuario. La ficha trae la descripcion completa, asi que
estas vacantes se puntuan con la misma informacion que las de un ATS.

## ATS que hay representados en el panel

{filas or '- (ninguno: el panel no tiene ahora vacantes venidas de un ATS)'}

## Cuanto aporta cada fuente, hoy

Contado sobre las vacantes que el panel ensena ahora mismo, no sobre lo que
recolecto una corrida concreta. Antes esta seccion salia de
`estadisticas.json` y se quedaba VACIA --encabezado impreso y nada debajo--
cada vez que el JSON no traia esas claves, que le dice al lector que la
respuesta no existe cuando si existe.

{chr(10).join(f'- **{k}**: {v} vacantes' for k, v in cif['por_fuente'].items())}

## Como agregar una empresa nueva

Abrir `app/fuentes_ats.py` y anadir el identificador de la empresa a la lista
del ATS que use. Si el identificador no existe, el API devuelve 404 y el
sistema lo descarta solo: no hay riesgo de meter datos falsos.
""",
        ["[[sistema/motor-de-recoleccion]]", "[[sistema/decision-el-ats-como-fuente-primaria]]", "[[01-wiki]]"],
        "Sistema", "Catalogo de fuentes",
    )

    nota(
        "sistema/decision-el-ats-como-fuente-primaria",
        "Decision: el ATS como fuente primaria",
        "decision", "hecho",
        ctx("por que el sistema prefiere las bolsas oficiales sobre los agregadores")
        + """
## Contexto

El problema central de buscar empleo con agregadores es la **vacante fantasma**:
sigue listada semanas despues de haberse cerrado. Postular a una es tiempo
perdido y no genera respuesta, lo que ademas desmoraliza.

## Decision

Tratar el API del ATS de cada empresa (Greenhouse, Lever, Ashby,
SmartRecruiters) como fuente primaria, y los agregadores solo como mecanismo de
descubrimiento.

## Por que

Cuando una empresa cierra una vacante, desaparece de su propio API de
inmediato. Por lo tanto: **si el API la devuelve hoy, esta abierta hoy.** La
verificacion no cuesta una peticion extra, viene incluida en la recoleccion.

## Consecuencia

- Las vacantes con `ats` no vacio se marcan `viva` con metodo `api-ats`.
- Las demas pasan obligatoriamente por [[sistema/verificador-de-vacantes]].
- Al deduplicar, si la misma vacante aparece en un ATS y en un agregador, gana
  la del ATS.

## Limite conocido

El API confirma que la vacante esta **publicada**, no que la empresa siga
revisando candidaturas activamente. Ninguna fuente publica puede confirmar eso.
""",
        ["[[sistema/catalogo-de-fuentes]]", "[[sistema/verificador-de-vacantes]]", "[[01-wiki]]"],
        "Sistema", "Decision: el ATS como fuente primaria",
    )

    nota(
        "sistema/clasificador-y-scoring",
        "Clasificador y scoring",
        "componente", "hecho",
        ctx("como el sistema decide si una vacante te sirve y cuanto")
        + f"""
## Que decide

Por cada vacante determina cuatro cosas y las registra con su motivo:

| Dimension | Valores posibles |
|---|---|
| `nivel` | practicas, junior, medio, excluido |
| `area` | ciber-ia, ciberseguridad, ia, ti-general, fuera |
| `modalidad` | remoto, presencial, hibrido |
| `elegible_mx` | si / no, mas `requiere_mudanza` |

## Como se reparte el score (0-100)

- **35 pts** nivel alcanzable (practicas 35, junior 26, medio 8, senior -25)
- **25 pts** relevancia del area (seguridad de IA 25, ciber 23, IA 19)
- **20 pts** viabilidad geografica (Monterrey 20, remoto abierto 17)
- **20 pts** coincidencia con las habilidades de tu CV ([[perfil/perfil-del-candidato]])
- **5 pts** recencia de publicacion
- **+8 extra** si cruza IA y seguridad, tu diferenciador raro
- **+3 extra** si la vacante esta en espanol

## Veredictos

- `aplicar-ya` — score 72 o mas
- `buen-fit` — 56 a 71
- `explorar` — 40 a 55
- `descartado` — menos de 40 (no llega al dashboard)

## Dos errores reales que se corrigieron

1. **`intern` casaba dentro de `internal`.** Una auditoria senior se colaba
   como vacante de practicas con 95 puntos. Se arreglo exigiendo limites de
   palabra en `nucleo.tiene_termino()`.
2. **Los limites de palabra rompieron el espanol.** `ciber` dejo de casar con
   `ciberseguridad`. Se anadio coincidencia por prefijo con el sufijo `*`.

Ambos casos viven como pruebas de regresion en `app/test_analisis.py`.

## Como reparte los veredictos ahora mismo

{chr(10).join(f'- **{k}**: {v}' for k, v in cif['por_veredicto'].items())}
""",
        ["[[perfil/perfil-del-candidato]]", "[[sistema/verificador-de-vacantes]]", "[[01-wiki]]"],
        "Sistema", "Clasificador y scoring",
    )

    nota(
        "sistema/verificador-de-vacantes",
        "Verificador de vacantes",
        "componente", "hecho",
        ctx("como se comprueba que cada vacante sigue viva")
        + f"""
## Las capas

0. **Al recolectar** — LinkedIn se verifica en el mismo momento en que se
   descarga su ficha publica.
1. **API del ATS** — coste cero. Si la bolsa oficial devolvio la vacante en
   esta corrida, esta publicada ahora. Es prueba primaria.
2. **HTTP directo** — se descarga la pagina y se buscan huellas de cierre
   (`no longer accepting applications`, `esta vacante ya no esta disponible`,
   404, redireccion al listado general) y huellas de vida (boton de postular).
3. **Chrome real** — para paginas con JavaScript o que exigen sesion. Es la
   unica capa que ve exactamente lo que veria un humano al abrir el enlace.

## Por que la capa 3 es imprescindible

OCC Mundial responde **403** a cualquier peticion directa a la ficha de una
vacante. Eso dejaba 109 vacantes de Monterrey — las mas importantes para
El usuario — sin verificar. Desde una pestana abierta en el dominio, las
peticiones del mismo origen si pasan.

El metodo se valido con un **control negativo**: se pidieron dos IDs
inexistentes y devolvieron 404 con una pagina de 29 KB, frente a los 200 y
~128 KB de una vacante real. La comprobacion distingue de verdad; no aprueba
todo lo que se le pone delante.

## Estados posibles

- `viva` — confirmada abierta
- `cerrada` — huella explicita de cierre; se archiva aparte, no se borra
- `sin-verificar` — exige sesion iniciada (LinkedIn) o no dio senal concluyente
- `inaccesible` — la pagina no respondio

## En que estado esta lo que ensena el panel

{chr(10).join(f'- **{k}**: {v}' for k, v in cif['por_verificacion'].items())}

## Lo que este componente NO puede garantizar

Que la empresa siga leyendo candidaturas. Una vacante puede estar publicada y
tener el proceso congelado. Por eso [[guias/plan-de-accion-30-dias]] insiste en
el contacto humano directo ademas del formulario.
""",
        ["[[sistema/decision-el-ats-como-fuente-primaria]]", "[[sistema/panel-de-vacantes]]", "[[01-wiki]]"],
        "Sistema", "Verificador de vacantes",
    )

    nota(
        "sistema/panel-de-vacantes",
        "Panel de vacantes (dashboard)",
        "componente", "hecho",
        ctx("el dashboard donde se ven y filtran todas las vacantes")
        + f"""
## Donde esta

Archivo `dashboard.html` en la raiz de la boveda. Se abre con doble clic: es un
unico archivo HTML con los datos embebidos, sin servidor ni conexion.

## Que permite

- Filtrar por prioridad, area, nivel, modalidad y estado de verificacion.
- Buscar texto libre en puesto, empresa, ciudad y tecnologias.
- Ordenar por mejor fit, mas reciente o empresa.
- Ver **por que** el sistema recomienda cada vacante (las razones del score).
- Marcar vacantes como aplicadas; el progreso se guarda en el navegador y
  sobrevive a que se regenere el panel.

## Vacantes que muestra ahora

**{cif['en_juego']}** en juego, de **{cif['panel']}** que el panel lista y
**{cif['historicas']}** que hay en el historico.

La diferencia entre las dos primeras son **{cif['descartadas_a_mano']}** que
El usuario ya descarto a mano, con el motivo escrito ("CDMX presencial", "pide
experiencia"). Siguen listadas a proposito, por si algun motivo deja de
aplicar, pero no cuentan como puertas por tocar; `postular.py` no se las vuelve
a ofrecer. `vacantes.json` exporta {cif['exportables']}: nueve menos que el
panel, porque ademas exige `elegible_mx = 1`.

## Como regenerarlo

```bash
python app/pipeline.py
python app/generar_dashboard.py
```
""",
        ["[[sistema/verificador-de-vacantes]]", "[[guias/plan-de-accion-30-dias]]", "[[01-wiki]]"],
        "Sistema", "Panel de vacantes",
    )


# ============================================================= NOTAS DE PERFIL

def notas_herramientas(est: dict | None = None) -> None:
    """Documenta el motor nuevo: red asincrona, almacen, tandas y paralelismo.

    `est` esta ahi por compatibilidad y no alimenta ninguna cifra: todas salen
    de `almacen.cifras_panel()`. Ver el porque en `notas_sistema`.
    """
    cif = cifras_panel()

    nota(
        "sistema/excavadora",
        "Excavadora: el motor de recoleccion",
        "componente", "hecho",
        ctx("el motor que sustituyo al pipeline secuencial")
        + f"""
## Que cambio y por que

El pipeline anterior descargaba y parseaba fuente por fuente, con hilos
bloqueantes. El cuello de botella no era el ancho de banda: era la espera.

La excavadora invierte el orden:

1. Cada fuente declara **que URLs quiere**, sin pedir nada todavia.
2. Se juntan todas — casi 4.000 — y salen en **una sola oleada concurrente**.
3. Cada respuesta se entrega al parser de su fuente.

## Resultado medido

| | Pipeline anterior | Excavadora |
|---|---|---|
| Vacantes crudas | 13.545 | **34.846** |
| Relevantes | 181 | **837** |
| URLs por corrida | ~700, por goteo | **3.977, en una oleada** |
| Tiempo | horas | **23 minutos** |

## Anadir una fuente nueva

Es una entrada en la lista `FUENTES` de `app/excavadora.py`: una funcion que
genera peticiones y otra que convierte la respuesta en vacantes. No hay que
tocar el orquestador.

```python
Fuente("mi_fuente", _mis_peticiones, _mi_parser)
```

## Dos oleadas

Hay cosas que no se pueden pedir hasta saber el resultado de lo anterior. Las
fichas de LinkedIn se piden con los identificadores que devolvio la busqueda,
asi que van en una segunda oleada.

## Como se ejecuta

```bash
python app/excavadora.py
```

Ver tambien [[sistema/red-asincrona]], [[sistema/almacen-sqlite]] y
[[sistema/trabajos-por-tandas]].
""",
        ["[[sistema/red-asincrona]]", "[[sistema/almacen-sqlite]]",
         "[[sistema/trabajos-por-tandas]]", "[[01-wiki]]"],
        "Sistema", "Excavadora: el motor de recoleccion",
    )

    nota(
        "sistema/red-asincrona",
        "Red asincrona y ritmo por sitio",
        "componente", "hecho",
        ctx("la capa de descarga concurrente y como evita que nos bloqueen")
        + """
## Tres controles, no uno

- **Limite global** (120 peticiones a la vez): para no ahogar la maquina.
- **Limite por sitio**: el que de verdad importa. El problema nunca es el
  total de peticiones, es golpear demasiado rapido a un mismo servidor.
- **Pausa minima entre peticiones al mismo sitio**: para las fuentes que
  limitan por tasa y no solo por concurrencia.

## Ritmo asignado a cada sitio

| Sitio | Simultaneas | Pausa |
|---|---|---|
| LinkedIn | 2 | 0,60 s |
| OCC Mundial | 8 | 0,10 s |
| Computrabajo | 6 | 0,15 s |
| RemoteOK, WeWorkRemotely | 3 | 0,20 s |
| Himalayas | 4 | 0,15 s |
| Resto (APIs de ATS) | 12 | sin pausa |

**Por que LinkedIn va tan despacio.** En una corrida medida devolvio solo 237
fichas de 510 busquedas: limita la tasa en cuanto se pagina a fondo. Tratarlo
igual que a una API de ATS es lo que hacia perder la mitad de los resultados.

**Por que los ATS van sueltos.** Greenhouse, Lever y Ashby publican APIs
pensadas para consultarse; no hay motivo para frenarlas.

## Cache

Cada URL se guarda en disco con vencimiento. Una segunda corrida el mismo dia
no vuelve a pedir lo que ya trajo.

## Codigo

`app/red.py`. El ritmo se ajusta en el diccionario `RITMO`.
""",
        ["[[sistema/excavadora]]", "[[sistema/catalogo-de-fuentes]]", "[[01-wiki]]"],
        "Sistema", "Red asincrona y ritmo por sitio",
    )

    nota(
        "sistema/almacen-sqlite",
        "Almacen: la memoria del sistema",
        "componente", "hecho",
        ctx("la base de datos que guarda el historial de vacantes")
        + f"""
## El problema que resuelve

Antes cada corrida reescribia `vacantes.json` entera. Eso tenia tres
consecuencias que solo se notan con el tiempo:

1. Lo que desaparecia de las fuentes se perdia sin rastro, asi que era
   imposible distinguir "esta vacante se cerro" de "el scraper fallo".
2. No habia forma de responder **"que salio nuevo desde ayer"**, que es la
   pregunta que de verdad importa cuando revisas a diario.
3. Marcar una vacante como aplicada vivia solo en el navegador.

## Como esta hecho

Dos tablas: `vacantes` con todo lo conocido de cada una, y `avistamientos`,
que registra en que corrida se vio cada vacante. De ahi salen solos los campos
`primera_vez`, `ultima_vez` y `veces`.

## Lo que responde sin esfuerzo

- **Nuevas desde la corrida anterior** → `almacen.nuevas_de_la_corrida()`
- **Desaparecidas** (candidatas a cerradas) → `almacen.desaparecidas()`
- **Tu seguimiento**, que sobrevive a cualquier recoleccion → `almacen.marcar_aplicada()`

## Estado actual

- Vacantes en el historial: **{cif['historicas']}** ({cif['panel']} en el panel,
  {cif['cerradas']} cerradas y archivadas)
- Archivo: `app/datos/ultrachamba.db`

## Consultarlo a mano

```bash
python app/almacen.py
```
""",
        ["[[sistema/excavadora]]", "[[sistema/panel-de-vacantes]]", "[[01-wiki]]"],
        "Sistema", "Almacen: la memoria del sistema",
    )

    nota(
        "sistema/trabajos-por-tandas",
        "Trabajos por tandas reanudables",
        "componente", "hecho",
        ctx("el mecanismo que permite reanudar un trabajo largo donde se quedo")
        + """
## El fallo que lo hizo necesario

Verificar 565 fichas de OCC en el navegador fallo tres veces seguidas:

1. Chrome bloqueo la lectura desde la red privada.
2. El proceso desacoplado se estrangulo al quedar la pestana en segundo plano.
3. El renderer se congelo por acumular peticiones.

El error de fondo no fue ninguno de esos tres. Fue **pedir 565 cosas de golpe y
no guardar nada hasta el final**, asi que cada fallo tiraba todo el trabajo.

## Como funciona

Cada elemento es una fila con estado en la base de datos:

```
pendiente -> en-curso -> hecho | fallido
```

- `siguiente_tanda()` reserva un grupo pequeno y lo marca en curso, para que
  dos ejecuciones simultaneas no hagan lo mismo dos veces.
- `completar()` guarda el resultado en cuanto llega, no al final.
- Si algo se rompe, la siguiente ejecucion **reanuda donde quedo**: lo hecho
  no se repite y lo pendiente no se pierde.
- Tras tres intentos fallidos, un elemento deja de reintentarse.

## Uso

```python
import tandas
tandas.encolar("occ_detalle", lista_de_ids)
lote = tandas.siguiente_tanda("occ_detalle", 40)
tandas.completar("occ_detalle", resultados)
tandas.progreso("occ_detalle")
```

## Ver el avance

```bash
python app/tandas.py occ_detalle
```
""",
        ["[[sistema/verificador-de-vacantes]]", "[[sistema/almacen-sqlite]]", "[[01-wiki]]"],
        "Sistema", "Trabajos por tandas reanudables",
    )

    nota(
        "sistema/analisis-en-paralelo",
        "Analisis en paralelo",
        "componente", "hecho",
        ctx("por que el clasificador se reparte entre varios nucleos")
        + """
## El cuello de botella se movio

Medido en una corrida real: de los 23 minutos que tardo la excavadora,
**13 se fueron en clasificar 15.927 vacantes**. Una vez resuelta la descarga,
el cuello de botella dejo de ser la red y paso a ser el calculo.

## Por que se puede repartir

El clasificador no comparte estado entre vacantes: cada una se analiza sola.
Eso lo hace repartible entre procesos sin ninguna coordinacion.

## Por que procesos y no hilos

El trabajo es de CPU, no de espera. Con hilos, el bloqueo global del
interprete de Python los serializaria y no se ganaria nada.

## Salvaguardas

- Por debajo de 2.000 vacantes no se paraleliza: crear procesos y mover los
  datos cuesta mas que analizarlas de una vez.
- Si el paralelismo falla por cualquier motivo del sistema, el trabajo se hace
  igual en un solo proceso. Nunca se queda sin analizar.

## Medir la ganancia en tu maquina

```bash
python app/analisis_paralelo.py
```
""",
        ["[[sistema/clasificador-y-scoring]]", "[[sistema/excavadora]]", "[[01-wiki]]"],
        "Sistema", "Analisis en paralelo",
    )

    nota(
        "sistema/deteccion-de-vacantes-fantasma",
        "Deteccion de vacantes fantasma",
        "componente", "hecho",
        ctx("como se detectan los anuncios que no contratan a nadie")
        + f"""
## Que es una vacante fantasma

Un anuncio publicado que no corresponde a una contratacion real. Entre el 18%
y el 27% de los anuncios en linea lo son; Greenhouse midio entre 18% y 22% en
su propia plataforma. Postular a una es tiempo perdido sin respuesta, y es lo
que mas desmoraliza en una busqueda larga.

## Por que este sistema puede detectarlas y los portales no

Las dos senales mas fuertes son la **antiguedad del anuncio** y su **historial
de republicacion**. Ningun portal las muestra: OCC no dice "esta lleva ocho
meses aqui". Pero esta base guarda cada avistamiento por corrida desde el
primer dia, asi que la antiguedad real y los ciclos de desaparicion y regreso
se calculan solos. **El historial es el activo; el detector solo lo lee.**

## Senales y su peso

| Senal | Puntos |
|---|---|
| Lleva mas de un año publicada | 55 |
| Muy antigua (180 dias) | 40 |
| Antigua (90 dias) | 25 |
| Algo antigua (45 dias) | 12 |
| Republicada tras desaparecer (2 o mas veces) | 26 |
| Empleador oculto ("Empresa Confidencial") | 20 |
| El mismo puesto repetido por la misma empresa | 17 |
| Publicada por agencia o bolsa, no por el empleador | 9 |
| Descripcion casi vacia | 8 |

Riesgo alto desde 55, medio desde 30. Todo punto lleva su motivo escrito: la
idea es que el usuario pueda discrepar mirando las razones, no acatar un
veredicto opaco.

## Calibracion: el primer intento no servia

La primera version daba 34 puntos a "muy antigua" y **ninguna vacante llegaba
a riesgo alto**, ni siquiera una de 1.437 dias. Se recalibro con los datos
reales de la base: una practica que lleva mas de un año abierta no esta
contratando a nadie, asi que la antiguedad extrema basta por si sola.

Casos reales encontrados tras recalibrar:

| Vacante | Empresa | Dias |
|---|---|---|
| LLM Data Scientist | Binance | 1.437 |
| Pioneer Talent Program | Binance | 997 |
| Software Engineer Intern | Ritual | 753 |
| Auditor TI Jr | Dresden Partners | 3.672 |

## El hueco que casi pasa desapercibido

**{cif['sin_fecha']} de {cif['panel']} vacantes ({cif['pct_sin_fecha']}%) no traen fecha
de publicacion**, porque muchas fuentes no la dan. Sin fecha, la senal
principal no aplica y la vacante salia con riesgo bajo aunque llevara años
abierta: eso es falsa tranquilidad, no ausencia de riesgo.

El respaldo sale del propio historial: si la base la ve desde hace N dias,
lleva **al menos** N dias abierta. Es una cota inferior, asi que nunca exagera.
Hoy el historial es corto y no suma puntos; en unas semanas de corridas se
vuelve la senal principal para esas {cif['sin_fecha']}. Mientras tanto se dice
explicitamente que la antiguedad no esta verificada.

## Aviso honesto sobre la madurez

La senal de republicacion necesita semanas de corridas para valer algo. Hoy
solo hay tres corridas con datos, asi que la senal viva es la antiguedad.

## Uso

```bash
python app/fantasma.py       # recalcula toda la base y muestra las peores
python app/test_fantasma.py  # 21 pruebas del detector
```

En el panel aparece como etiqueta en la tarjeta, como filtro rapido
("Ocultar posibles fantasmas") y como cifra en la cabecera.
""",
        ["[[sistema/almacen-sqlite]]", "[[sistema/panel-de-vacantes]]", "[[01-wiki]]"],
        "Sistema", "Deteccion de vacantes fantasma",
    )

    nota(
        "sistema/corpus-para-notebooklm",
        "Corpus para NotebookLM",
        "componente", "hecho",
        ctx("como se consultan las 1.266 descripciones que no caben en contexto")
        + """
## El problema que resuelve

El panel responde preguntas de filtro ("las de Monterrey sin mudanza"), pero
no responde preguntas sobre el CONTENIDO de los anuncios: que piden de verdad,
que se repite, que es indispensable y que solo deseable. Eso exige leer 1.266
descripciones —unas 615.000 palabras— que no caben de golpe en la memoria de
trabajo de ningun agente.

## Por que NotebookLM y no contar palabras

El sistema ya cuenta terminos en `medir_habilidades()`. La diferencia es que
NotebookLM lee la frase alrededor del termino: distingue "indispensable" de
"se valorara", y **cita el anuncio concreto** del que sale cada afirmacion.
Eso convierte una impresion en una afirmacion rastreable.

## Que se exporta

```bash
python app/exportar_corpus.py
```

Genera `corpus-notebooklm/` con un archivo por area:

| Archivo | Vacantes | Palabras |
|---|---|---|
| 01-ciberseguridad | 242 | 90.888 |
| 02-inteligencia-artificial | 306 | 171.317 |
| 03-ti-general | 718 | 352.591 |

Cada bloque empieza con `VACANTE:` e incluye empresa, ubicacion, modalidad,
nivel, salario y enlace, para que cualquier respuesta pueda rastrearse hasta
el anuncio real. Se excluyen las descripciones de menos de 200 caracteres:
sin texto no hay nada que leer.

## Regla de privacidad

NotebookLM **exige compartir el cuaderno con "cualquiera con el enlace"**. Por
eso aqui solo va texto que ya era publico: anuncios de empleo publicados en
internet. **El CV, el correo y el telefono no se suben nunca.**

## Fallo que dejo el guardarrail

La primera version pedia una columna `enlace` que en la tabla se llama `url`.
No fallo: dejo los 1.266 enlaces como "no indicado" en silencio. Ahora un
`assert` comprueba que las columnas imprescindibles existan antes de exportar.
""",
        ["[[sistema/almacen-sqlite]]", "[[guias/como-usar-el-sistema]]", "[[01-wiki]]"],
        "Sistema", "Corpus para NotebookLM",
    )


def notas_diseno() -> None:
    """El sistema visual del panel: de donde sale y como se aplica."""

    nota(
        "sistema/sistema-de-diseno",
        "Sistema de diseno del panel",
        "componente", "hecho",
        ctx("los colores, la tipografia y las reglas visuales del panel")
        + """
## De donde sale

**El lenguaje visual** se tomo de [copula.agency](https://copula.agency),
estudiada con el navegador el 2026-08-16. **La paleta la definio el usuario**;
no es la de Copula, que usa naranja y azul electrico.

## Lo que se midio en el sitio de referencia

No se estimo a ojo: se leyeron los estilos ya calculados en la pagina.

| Elemento | Valor real |
|---|---|
| Tipografia display | **Bebas Neue** 400, usada a 69, 90 y hasta 226 px |
| Tipografia de texto | **Mulish** variable 200-1000 |
| Colores de fondo | naranja `#FC5100`, azul `#0501DE`, crema `#F4EFE9` |
| Radios | 30 px, 150 px, 50% y pildora completa |
| **Sombras** | **ninguna** — cero `box-shadow` en toda la pagina |

## El hero, calcado en estructura

La portada replica la del sitio de referencia, elemento por elemento:

| Copula | Aqui |
|---|---|
| Barra superior con logo y boton circular `+` | `ultrachamba` + boton que baja a los filtros |
| Texto pequeño arriba a la izquierda | nombre, ciudad y area |
| `YOUR / DIGITAL / AGENCY` apilado a pantalla completa | `TU / PROXIMA / CHAMBA` |
| Asterisco azul | asterisco morado, girando despacio |
| Blob con `LET'S BOND` | blob con el numero de vacantes para aplicar ya |
| Pestaña negra lateral `W. Honors` | pestaña morada con el total de vivas |
| Punto flotante | igual, flotando |

Las dos formas (asterisco y blob) estan dibujadas como SVG en el propio
componente, no son imagenes: escalan sin perder nitidez y toman el color de
la paleta.

## Los cinco rasgos que se copiaron

1. **Bloques de color a sangre.** Cada seccion ocupa el ancho completo con un
   color solido y corte duro contra la siguiente. Sin degradados.
2. **Display condensada en mayusculas.** Los titulos son tipografia estrecha,
   grande y en caja alta. Es lo que da caracter.
3. **Etiquetas de seccion con asterisco.** Un `✳` seguido de versalitas
   espaciadas, arriba a la izquierda de cada bloque.
4. **Diseno plano, sin sombras.** La profundidad la da el color y el borde,
   nunca el relieve. Esto se respeto al pie de la letra.
5. **Formas de pildora.** Botones, etiquetas y campos con radio completo.

## La paleta, y que hace cada color aqui

| Uso | Color | Hex | Donde se aplica en el panel |
|---|---|---|---|
| Fondo principal | Blanco humo | `#F8F7FC` | fondo de la pagina |
| Fondo secundario | Blanco lavanda | `#F3F0FA` | campos, etiquetas neutras, tarjeta aplicada |
| Tarjetas | Blanco | `#FFFFFF` | fondo de cada vacante |
| Morado principal | Violeta moderno | `#6D28D9` | boton de postular, score alto, filtro activo |
| Morado secundario | Lavanda intensa | `#8B5CF6` | hover, borde al pasar el raton, score medio |
| Morado suave | Lila claro | `#DDD6FE` | fondo de las etiquetas de nivel (practicas, junior) |
| Morado oscuro | Purpura profundo | `#3B0764` | cabecera y pie a sangre, titulos de vacante |
| Texto principal | Gris casi negro | `#1F2937` | cuerpo |
| Texto secundario | Gris medio | `#6B7280` | empresa, ubicacion, metadatos |
| Bordes | Gris lavanda | `#E5E1F2` | separadores y contorno de tarjeta |
| Exito | Verde suave | `#10B981` | verificada viva, Monterrey sin mudanza |
| Advertencia | Ambar | `#F59E0B` | sin confirmar, zona gris, score bajo |
| Error | Rojo coral | `#EF4444` | exige mudarse, pide anos que no tienes |
| Info | Azul violeta | `#6366F1` | fuente y habilidades: datos complementarios |

## Equivalencias que hubo que inventar

La tabla original describia usos genericos. Estos tres no tenian equivalente
directo en el panel y se decidieron asi:

- **"Info / datos complementarios"** → las etiquetas de **fuente** (occ,
  linkedin, greenhouse) y de **habilidades coincidentes**. Son informacion de
  apoyo: importan, pero no deben competir con el titulo ni con el veredicto.
- **"Morado oscuro / titulos y elementos premium"** → la **cabecera y el pie
  a sangre**, ademas del titulo de cada vacante. Es el color que estructura la
  pagina, igual que el naranja estructura la de Copula.
- **"Morado suave / fondos de etiquetas"** → solo las etiquetas de **nivel**
  (practicas, junior). Se reservo para eso a proposito: si se usara en todas,
  dejaria de senalar nada.

## Regla de color que se sigue

Un color = un significado. Verde solo dice "esto esta bien confirmado o no
exige mudanza". Rojo solo dice "esto te bloquea". Morado es la marca y la
accion. Si un color empieza a significar dos cosas, deja de comunicar.

## Donde vive

`panel.html`, en las variables CSS del bloque `:root`. Cambiar un color ahi lo
cambia en todo el panel. La interfaz no lleva datos dentro: los pide al
servidor. Ver [[sistema/panel-de-vacantes]].

## Esta hecho en React

El panel es una aplicacion **React 18**, dividida en componentes:
`Hero`, `Filtros`, `Tarjeta`, `Etiquetas`, `Asterisco` y `Blob`.

**Sin paso de compilacion.** No hay npm, ni webpack, ni Babel. Se usa `htm`,
una libreria de 1,2 KB que permite escribir plantillas con literales de
plantilla en vez de JSX. Editar el panel es abrir el archivo y guardar.

**Sin CDN.** React, ReactDOM y htm estan descargados en `app/vendor/` y los
sirve el propio servidor local. Son 140 KB y hacen que el panel funcione sin
conexion. Lo unico que necesita internet son las tipografias, y sin ellas
degrada a Oswald y Arial Narrow.

Por que React aqui: el panel tiene estado que cambia constantemente — filtros,
busqueda, orden, marcado de aplicadas — y antes eso se manejaba reconstruyendo
el HTML a mano en cada cambio. Con componentes, cada parte se redibuja sola
cuando cambia lo suyo.

## Tipografia

Bebas Neue y Mulish se cargan desde Google Fonts, con respaldo a Oswald y
Arial Narrow por si no hay conexion. El panel sigue siendo legible sin
internet, solo pierde el caracter de la display.
""",
        ["[[sistema/panel-de-vacantes]]", "[[01-wiki]]"],
        "Sistema", "Sistema de diseno del panel",
    )


def notas_investigacion() -> None:
    """Lo aprendido mirando lo que ya existe, con los numeros comprobados."""

    nota(
        "sistema/decision-que-tomamos-del-software-libre",
        "Decision: que tomamos del software libre y que no",
        "decision", "hecho",
        ctx("la evaluacion de las herramientas abiertas que ya resuelven parte de esto")
        + """
## Por que existe esta nota

Este sistema se construyo desde cero sin mirar antes que habia publicado. Fue
un error. Esta nota corrige esa omision y deja constancia de lo evaluado, con
numeros comprobados el 2026-08-15, no con impresiones.

## Lo que hay

| Proyecto | Estrellas | Licencia | Ultimo cambio |
|---|---|---|---|
| speedyapply/JobSpy | 4.093 | MIT | 2026-02-18 |
| spinlud/py-linkedin-jobs-scraper | 492 | MIT | 2026-08-10 |
| kalil0321/ats-scrapers | 128 | MIT | 2026-08-07 |
| hendrixfreire/linkedin-job-scraper | 75 | MIT | 2026-08-04 |

## Lo que ADOPTAMOS: el directorio de empresas

`ats-scrapers` publica listas de empresas por plataforma de contratacion.
Comprobado descargandolas:

| Plataforma | Empresas |
|---|---|
| Greenhouse | 6.031 |
| Ashby | 3.448 |
| SmartRecruiters | 2.747 |
| Lever | 2.402 |
| **Total** | **14.628** |

La lista que habia aqui estaba escrita a mano: 280 nombres adivinados.

**Medicion sobre una muestra aleatoria de 300 empresas nuevas:**

- 257 bolsas vivas → **86% de acierto** (la lista a mano acertaba el 29%)
- 8.046 vacantes en 6 segundos
- Extrapolado a las 5.977 nuevas: **~5.120 bolsas vivas, ~160.000 vacantes**

Efecto en el sistema: de 3.977 a **18.325 URLs** por corrida.
Ver [[sistema/directorio-de-empresas]].

## Lo que NO adoptamos, y por que

### Su dataset hospedado de 4,8 millones de vacantes

Existe de verdad y responde sin clave: 4.854.656 filas, 65 fuentes. Pero se
comprobo antes de confiar en el, y tiene dos defectos que lo descartan como
fuente principal:

1. **El campo de pais no sirve para Mexico.** En la porcion de iCIMS, 32
   vacantes tienen "Monterrey, NLE, MX" escrito en la ubicacion y su campo
   `country_iso` viene **vacio**. Filtrar por pais perderia todas.
2. **El campo de remoto viene nulo.** En iCIMS, las 220.170 filas traen
   `is_remote` sin poblar.

Ademas **tiene 8 dias de antiguedad** (generado el 2026-08-07). Para postular,
una vacante de hace 8 dias puede estar cerrada. La verificacion en vivo de
[[sistema/verificador-de-vacantes]] sigue siendo necesaria.

**Aun asi enseno algo:** en esa porcion aparecio **MSCI con oficina en
Monterrey**, con analistas de datos, riesgo y practicas. Usa iCIMS, una
plataforma que este sistema no consulta. Era un empleador invisible.

### JobSpy

Cubre LinkedIn, Indeed, Glassdoor, Google y ZipRecruiter, y soporta Indeed
Mexico. **No cubre OCC ni Computrabajo**, que son las dos bolsas donde estan
de verdad las practicas de Monterrey. Ninguna herramienta publica las cubre:
esa parte no es reemplazable.

Su documentacion **confirma de forma independiente** una medicion hecha aqui:
LinkedIn limita la tasa alrededor de la pagina 10 con una sola IP. Aqui se
midio exactamente eso — 237 fichas de 510 busquedas — y por eso existe el
ritmo por sitio de [[sistema/red-asincrona]].

Tambien documentan que **todos los portales topan en unos 1.000 resultados por
busqueda**: por eso ampliar el numero de consultas rinde mas que ampliar
paginas.

## Lo que ninguno hace

Ninguna de estas herramientas puntua contra un CV concreto, ni sabe que
El usuario no puede mudarse de Monterrey, ni que no tiene tres anos de
experiencia. Eso es [[sistema/clasificador-y-scoring]] y no existe fuera de
aqui.

## Pendiente de incorporar

- **Indeed Mexico**, via JobSpy. Es una fuente grande que falta.
- **Workday, SuccessFactors, iCIMS y Oracle**: cuatro plataformas sin cubrir,
  y son las de los corporativos grandes de Monterrey.
""",
        ["[[sistema/directorio-de-empresas]]", "[[sistema/red-asincrona]]",
         "[[sistema/clasificador-y-scoring]]", "[[01-wiki]]"],
        "Sistema", "Decision: que tomamos del software libre y que no",
    )

    nota(
        "sistema/plataformas-de-corporativos",
        "Plataformas de corporativos: Workday, Oracle, iCIMS y SuccessFactors",
        "componente", "hecho",
        ctx("las cuatro plataformas de contratacion que usan las empresas grandes")
        + """
## Por que se anadieron

El sistema no tocaba ninguna de las cuatro. Se descubrio revisando un dataset
abierto: alli aparecio **MSCI con oficina en Monterrey**, con puestos de
analista de datos, riesgo y practicas, publicados en **iCIMS**. Era un
empleador completamente invisible para este buscador.

No es un caso aislado: son las plataformas que usan los corporativos grandes,
que es justo el tipo de empresa con presencia en Monterrey.

## Volumen que suman

| Plataforma | Vacantes | Empresas |
|---|---|---|
| Workday | 839.633 | 3.530 |
| SuccessFactors | 320.799 | 1.392 |
| Oracle | 296.978 | 1.279 |
| iCIMS | 220.170 | 2.498 |
| **Total** | **~1.677.000** | **8.699** |

## Como se consulta cada una

Todos los endpoints se verificaron con peticiones reales el 2026-08-15.

- **Workday** — POST a `/wday/cxs/{tenant}/{sitio}/jobs` con el filtro en el
  cuerpo. Devuelve JSON con `total` y `jobPostings`. **Es el unico que no
  admite GET**, y por eso [[sistema/red-asincrona]] aprendio a hacer POST.
- **Oracle** — GET al API REST `recruitingCEJobRequisitions`. JSON limpio con
  `TotalJobsCount` y `requisitionList`.
- **iCIMS** — HTML en `/jobs/search`. No tiene API publica.
- **SuccessFactors** — HTML en `{empresa}.jobs2web.com/search`.

## Dos detalles que costaron

1. **iCIMS colaba enlaces de navegacion.** El primer parser recogia "Welcome
   page" y "Log back in!" como si fueran vacantes: 1.897 resultados de los
   cuales casi la mitad eran basura. Se arreglo exigiendo que la ruta lleve un
   identificador numerico de vacante. Quedaron 1.019 reales.
2. **Workday no publica fechas, publica frases.** Dice "Posted 12 Days Ago" en
   vez de una fecha, asi que hay que convertirlo para poder ordenar por
   recencia.

## Cuantas empresas se consultan

No todas. El directorio trae 8.699 y pedirlas todas en cada corrida
multiplicaria el tiempo sin aportar mucho, porque la mayoria no contrata en
Mexico ni en remoto abierto. Los topes estan en `TOPE`, dentro de
`app/fuentes_ats_extra.py`, y se pueden subir cuando la corrida completa sea
lo bastante rapida.

## Codigo

`app/fuentes_ats_extra.py`. Se prueba solo con:

```bash
python app/fuentes_ats_extra.py
```
""",
        ["[[sistema/directorio-de-empresas]]", "[[sistema/red-asincrona]]",
         "[[sistema/decision-que-tomamos-del-software-libre]]", "[[01-wiki]]"],
        "Sistema", "Plataformas de corporativos (Workday, Oracle, iCIMS, SuccessFactors)",
    )

    nota(
        "sistema/directorio-de-empresas",
        "Directorio de empresas por plataforma",
        "componente", "hecho",
        ctx("de donde sale la lista de empresas cuyas bolsas se consultan")
        + """
## Que hace

Descarga y cachea las listas de empresas por plataforma de contratacion que
publica el proyecto abierto `kalil0321/ats-scrapers` (licencia MIT), y las
entrega a [[sistema/excavadora]] como identificadores a consultar.

## Por que sustituyo a la lista escrita a mano

La lista anterior eran 280 nombres adivinados; solo 80 respondian. Medido
sobre 300 empresas del directorio: **86% de bolsas vivas** frente al 29%.

| Plataforma | Empresas |
|---|---|
| Greenhouse | 6.031 |
| Ashby | 3.448 |
| SmartRecruiters | 2.747 |
| Lever | 2.402 |

## Salvaguarda

Si el directorio no esta disponible, el sistema cae automaticamente a la lista
local y sigue funcionando. Nunca se queda sin fuentes.

## El coste que trajo, y como se paga

Multiplicar por seis el corpus haria que el analisis completo tardara mas de
media hora. Por eso existe el **prefiltro**: una sola pasada de expresion
regular sobre titulo y ubicacion, antes del analisis caro.

Esta escrito para no perder nada relevante. Comprobado contra el panel:
**conserva el 98,9% y no descarta ni una vacante con puntuacion 56 o mas.**

## Codigo

`app/directorio.py`. La cache dura 7 dias.
""",
        ["[[sistema/excavadora]]", "[[sistema/decision-que-tomamos-del-software-libre]]",
         "[[01-wiki]]"],
        "Sistema", "Directorio de empresas por plataforma",
    )

    nota(
        "sistema/decision-scoring-por-palabras-vs-semantico",
        "Decision: puntuar por palabras o por significado",
        "decision", "en-progreso",
        ctx("por que el scoring usa reglas y no un modelo de lenguaje")
        + """
## Lo que dice la investigacion

Los trabajos publicados sobre emparejamiento de CV y vacante coinciden: los
modelos de lenguaje que comparan **significado** superan a los metodos por
palabras clave y TF-IDF. Un estudio reporta una reduccion de errores de
emparejamiento **superior al 30%**, y un modelo Sentence-BERT ajustado supera
tanto a TF-IDF como a BERT sin ajustar.

El motivo es claro: contar palabras no entiende sinonimos ni contexto.
"Respuesta a incidentes" y "incident handling" son lo mismo y el conteo no lo
sabe.

## Por que aqui NO se cambio todavia

Tres razones, por orden de peso:

1. **Las restricciones duras no admiten aproximacion.** Que el usuario no pueda
   mudarse de Monterrey, o que una vacante exija cinco anos, son hechos
   binarios. Un parecido semantico del 0,82 no responde "¿puede o no puede?".
   Esas reglas deben seguir siendo exactas y auditables.
2. **La auditabilidad se perderia.** Hoy cada recomendacion muestra sus
   razones y se puede discutir. Una puntuacion de similitud es un numero sin
   explicacion, y ya se detectaron aqui cinco errores de clasificacion
   precisamente por poder leer los motivos.
3. **El coste.** Anadir un modelo de este tipo trae cientos de megabytes de
   dependencias a una herramienta que hoy corre con lo que ya hay instalado.

## La decision

**Hibrido, y en este orden:**

- Las reglas exactas siguen decidiendo lo binario: geografia, nivel, anos
  exigidos, dominio. Ver [[sistema/clasificador-y-scoring]].
- El parecido semantico se anadiria solo para **ordenar por relevancia** entre
  las que ya pasaron los filtros duros, que es donde los sinonimos importan y
  donde equivocarse no descarta a nadie.

## Como se comprobaria que mejora

Con el mismo metodo que ya se usa aqui: un banco de casos reales. Se marcan a
mano 50 vacantes como buenas o malas, y se compara el orden que produce cada
metodo. Sin esa medicion, cambiar seria una corazonada.

[COMPLETAR: ejecutar esa comparacion antes de adoptar el modelo semantico]
""",
        ["[[sistema/clasificador-y-scoring]]", "[[perfil/perfil-del-candidato]]", "[[01-wiki]]"],
        "Sistema", "Decision: puntuar por palabras o por significado",
    )


def notas_perfil() -> None:
    nota(
        "perfil/perfil-del-candidato",
        "Perfil del candidato",
        "producto", "hecho",
        ctx("quien es el candidato y que busca")
        + f"""
## Datos

- **Nombre:** {CANDIDATO['nombre']}
- **Correo:** {CANDIDATO['correo']}
- **Telefono:** {CANDIDATO['telefono']}
- **Ciudad:** {CANDIDATO['ciudad']}
- **LinkedIn:** {CANDIDATO['linkedin']}
- **GitHub:** {CANDIDATO['github']}
- **Estudios:** {CANDIDATO['grado']}
- **Idiomas:** espanol {CANDIDATO['espanol']}, ingles {CANDIDATO['ingles']}

## Objetivo

{CANDIDATO['titulo_objetivo']}

## CV

Esta copia NO incluye el CV de nadie. Deja el tuyo en PDF en la raiz del
proyecto y el sistema lo adjunta solo cuando prepara un correo.

## Que sabe hacer, con evidencia

Sale de `perfil.LOGROS`. Si aun dice EJEMPLO, rellenalo: es lo unico que los
correos tienen permitido afirmar.

{chr(10).join('- ' + l for area in LOGROS for l in LOGROS[area])}

## Certificaciones

Obtenidas: {', '.join(n for n, _ in CERTIFICACIONES['obtenidas']) or 'ninguna declarada'}

En preparacion (se nombran SIEMPRE con su estado, nunca como obtenidas):
{chr(10).join('- ' + n + ' — ' + estado for n, estado in CERTIFICACIONES['pendientes']) or '- ninguna'}
""",
        ["[[perfil/fortalezas-diferenciadoras]]", "[[perfil/brechas-y-como-cerrarlas]]", "[[01-wiki]]"],
        "Perfil", "Perfil del candidato",
    )

    nota(
        "perfil/fortalezas-diferenciadoras",
        "Fortalezas diferenciadoras",
        "producto", "hecho",
        ctx("que tipo de fortalezas diferencian a un perfil junior de seguridad")
        + """
Esta nota NO afirma nada sobre ti: el proyecto se comparte sin el perfil de
nadie. Lo de abajo es que TIPO de fortaleza diferencia, para que reconozcas las
tuyas. Lo que de verdad tengas va en `perfil.LOGROS`, y de ahi lo toman los
correos.

## 1. Entregables, no teoria

Muchos perfiles junior llegan con certificaciones y cero documentos. Si has
producido algo que otra persona tuvo que leer y aplicar --una politica, una
auditoria, un plan de remediacion-- eso es el trabajo del puesto, ya hecho una
vez.

**Como usarlo:** menciona el numero. Cuantos entregables, cuantos hallazgos,
cuantos sistemas. Los numeros pasan los filtros automaticos y se recuerdan.

## 2. Los cruces raros

Hay mucha gente en ciberseguridad y mucha en IA; en la interseccion hay pocas.
Lo mismo pasa con seguridad y nube, o seguridad y datos. Si tienes un cruce,
ahi compites contra menos gente.

**Como usarlo:** es el gancho de apertura del correo, no un detalle al final.
Ver [[guias/correos-de-postulacion]].

## 3. Automatizacion demostrable

Automatizar una tarea y dejar evidencia de cada cambio separa "sabe de
seguridad" de "puede operar seguridad".

## 4. Idiomas

Para una empresa que quiera cubrir una region, un hablante nativo con el
idioma tecnico suficiente cubre un requisito que muchos candidatos no cumplen.
Declara tu nivel real, en `perfil.CANDIDATO`: inflarlo se cae en la entrevista.

## 5. Saber escribir

Runbooks, politicas, planes de remediacion. Muchos perfiles tecnicos junior no
saben escribir. En GRC, escribir ES el trabajo.
""",
        ["[[perfil/perfil-del-candidato]]", "[[guias/correos-de-postulacion]]", "[[01-wiki]]"],
        "Perfil", "Fortalezas diferenciadoras",
    )

    nota(
        "perfil/brechas-y-como-cerrarlas",
        "Brechas y como cerrarlas",
        "producto", "en-progreso",
        ctx("que falta en el perfil y la accion concreta para cubrirlo")
        + """
Esta nota viene SIN diagnostico: el proyecto se comparte sin el perfil de
nadie, y las brechas de otra persona no son las tuyas. Abajo estan las que
suelen pesar en un perfil junior de seguridad; quedate con las que te apliquen
y borra el resto.

## Brecha habitual 1 — El idioma bloquea el remoto internacional

**Impacto:** alto si buscas remoto fuera de tu pais. La entrevista tecnica en
otro idioma es donde se cae, y no por gramatica: por no haber narrado nunca el
trabajo propio en ese idioma.

**Accion:** practicar en voz alta 20 minutos diarios contando TUS proyectos, no
estudiando gramatica. Grabarse y volver a escucharse.
Ver [[guias/entrevista-tecnica-en-ingles]].

## Brecha habitual 2 — Sin evidencia publica de trabajo de deteccion

**Impacto:** alto para vacantes de Blue Team. Una certificacion en preparacion
es una promesa, no una prueba.

**Accion:** montar un laboratorio pequeno y publicarlo. Varios fabricantes dan
tenants de desarrollador gratuitos: levantar un SIEM, generar alertas y
escribir unas cuantas reglas propias, con un README que explique que detecta
cada una y por que.

## Brecha habitual 3 — El repositorio no respalda lo que dice el CV

**Impacto:** medio-alto. Quien te evalua abre tu GitHub. Si el perfil promete
algo que el repositorio no demuestra de forma legible, la credibilidad cae.

**Accion:** README con capturas, resultados numericos y dos parrafos para
alguien que no conoce el proyecto. Ver [[guias/optimizar-linkedin-y-github]].

## Brecha habitual 4 — Ninguna certificacion terminada

**Impacto:** medio. Hasta que se aprueba, una certificacion agendada no pasa
los filtros automaticos. Elige una que encaje con el trabajo que buscas, no la
de mas prestigio.

## Brecha habitual 5 — La red de contactos sin activar

**Impacto:** suele ser el mas alto, y el mas barato de cerrar.

**Accion:** ver [[guias/plan-de-accion-30-dias]]. Muchas practicas no se llenan
por formulario, se llenan por contacto.
""",
        ["[[guias/plan-de-accion-30-dias]]", "[[guias/optimizar-linkedin-y-github]]", "[[01-wiki]]"],
        "Perfil", "Brechas y como cerrarlas",
    )

    nota(
        "perfil/restricciones-de-busqueda",
        "Restricciones de busqueda",
        "producto", "hecho",
        ctx("los limites duros que filtran que vacantes tienen sentido")
        + f"""
## Restricciones declaradas

| Restriccion | Valor | Efecto en el sistema |
|---|---|---|
| Presencial | Solo area metropolitana de Monterrey | +20 pts; fuera del AMM se marca `requiere_mudanza` |
| Remoto | Mundial, si aceptan contratar desde Mexico | Se descarta todo "Remote - USA" y equivalentes |
| Nivel | Practicas o inicial | Titulos senior/lead/manager quedan excluidos |
| Ingles | {CANDIDATO['ingles']} | Vacantes en espanol suman 3 pts |
| Visa | Requeriria patrocinio | Presencial en el extranjero se descarta |
| Zona horaria | {CANDIDATO['zona_horaria']} | Compatible con America y con la manana europea |

## Lo que el sistema descarta y por que

- **"Remote - USA" / "US - Remote"** — remoto cerrado a residentes de EEUU.
- **Security clearance / TS-SCI / polygraph** — exigen ciudadania estadounidense.
- **Presencial en el extranjero** — requeriria visa de trabajo, poco realista
  para unas practicas.
- **Titulos senior, lead, manager, director** — fuera de nivel.

## Zona gris que SI se muestra, marcada

- Remoto sin restriccion declarada: elegible, pero hay que confirmarlo al postular.
- Presencial en Mexico fuera de Monterrey: elegible, pero exige mudarse.
""",
        ["[[sistema/clasificador-y-scoring]]", "[[perfil/perfil-del-candidato]]", "[[01-wiki]]"],
        "Perfil", "Restricciones de busqueda",
    )

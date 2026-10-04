"""
Notas del seguimiento: que pasa DESPUES de darle a Enviar.

Por que en un archivo aparte. `generar_obsidian_estrategia.py` documenta como
se decide a quien escribir y como se redacta. Esto documenta el tramo
siguiente, que es otro problema: una candidatura enviada y olvidada vale lo
mismo que una no enviada, y hasta el 24 de agosto de 2026 el sistema no tenia
forma de saber si alguien habia contestado.

La nota de procesos en marcha se genera desde la BASE, no a mano: es la unica
forma de que no envejezca en silencio, que es como envejecen las notas de
estado.
"""
from __future__ import annotations

from generar_obsidian import ctx, nota


def notas_seguimiento(est: dict | None = None) -> None:
    """Las tres notas del seguimiento automatico (24 de agosto de 2026)."""

    # ------------------------------------------------------------------ 1 --
    nota(
        "sistema/seguimiento-de-candidaturas",
        "Seguimiento: quien contesto y quien calla",
        "componente", "hecho",
        ctx("como el sistema se entera solo de lo que pasa tras enviar un correo")
        + """
## El problema que resuelve

La columna `enviada` solo se rellenaba si el usuario pulsaba "ya la envie" en
el panel. Es decir: el sistema le pedia que hiciera de secretario de si mismo,
justo en el punto del proceso donde ya habia hecho el trabajo dificil.

Peor: no habia forma de saber si alguien habia CONTESTADO. Una candidatura
enviada y olvidada rinde lo mismo que una no enviada.

`seguimiento.py` lo mira en Gmail, con el permiso de lectura que se autorizo
ese mismo dia — ver [[sistema/gmail-como-fuente]].

## Las tres cosas que hace

1. **Emparejar.** Busca en Enviados el correo que corresponde a cada
   candidatura y le pega su hilo. Anota la fecha REAL del envio, no la del
   dia en que alguien se acordo de marcarlo.
2. **Revisar.** Recorre cada hilo anclado y mira si entro algo que no salio de
   esta cuenta. Si entro, `respondida`; si no, cuenta los dias callados. A los
   7 el estado pasa a `silencio`.
3. **Adoptar.** Da de alta hilos que el usuario movio a mano antes de que esto
   existiera. Sin esto, el seguimiento cubriria solo lo que genero la cola —
   seria un seguimiento de la cola, no de su busqueda.

## La decision que sostiene todo: anclar al HILO

Se guarda el `threadId` de Gmail, no el asunto.

El asunto lo reescribe quien contesta: le pone "Re:", "RV:", lo traduce, o lo
cambia entero al reenviarlo a otro departamento. Si el ancla fuera el asunto,
el rastro se perderia **en silencio**, que es la peor forma de perderlo: no
hay error, no hay aviso, simplemente esa candidatura deja de existir para el
sistema. El hilo sobrevive a todo eso.

## Estados que escribe, y los que no toca

| Estado | Quien lo pone |
|---|---|
| `enviada`, `acuse`, `silencio`, `rebote` | el seguimiento |
| `entrevista`, `oferta`, `rechazo`, `descartada` | el usuario |

La regla es dura a proposito: **una heuristica no pisa un juicio humano**. Si
el estado actual no esta en la lista de arriba, el modulo lo deja como esta.

## Por que existe el estado `rebote`

Un correo devuelto importa mas que uno sin contestar: significa que la
direccion era mala. El sistema ya avisaba de que un correo
`inferido-por-patron` puede rebotar — ver [[sistema/correos-en-frio]] — pero
nadie se enteraba de que rebotaba de verdad. Ahora se detecta por el
remitente (`mailer-daemon`, `postmaster`).

## Uso

```bash
python app/seguimiento.py                        # emparejar + revisar
python app/seguimiento.py --adoptar "to:empresa.com"
```

En el panel aparece dentro de la pestaña ★ Plan de hoy, debajo de la cola.
""",
        ["[[sistema/gmail-como-fuente]]", "[[sistema/cola-de-candidaturas]]",
         "[[perfil/procesos-en-marcha]]",
         "[[sistema/procesos-que-no-pasan-por-el-correo]]", "[[01-wiki]]"],
        "Sistema", "Seguimiento de candidaturas",
    )

    # ------------------------------------------------------------------ 2 --
    nota(
        "sistema/gmail-como-fuente",
        "Gmail: borradores, lectura y sus dos cicatrices",
        "componente", "hecho",
        ctx("como el sistema escribe y lee el correo del usuario")
        + """
## Que permisos tiene, y que NO tiene

| Permiso | Para que |
|---|---|
| `gmail.compose` | crear y reescribir borradores |
| `gmail.readonly` | leer, para saber quien contesto |

**No se pide `gmail.send`.** El sistema deja el correo escrito y esperando; el
envio es un gesto del usuario. Un sistema que manda correos solo en nombre de
alguien es un sistema del que hay que desconfiar.

Aviso que conviene no olvidar: la pantalla de consentimiento de Google etiqueta
`gmail.compose` como "gestionar borradores y **enviar** correos". Es su texto
estandar — no existe una variante de solo-borrador — asi que el permiso
concedido lo permitiria. **La garantia es el codigo, no la etiqueta.**

La cuenta es la misma en las tres puntas que importan: el token autorizado, el
campo `correo` de `perfil.py`, y la direccion impresa en el PDF del CV que se
adjunta. Si una de las tres se desviara, las respuestas caerian en un buzon
que nadie mira.

## Responder DENTRO del hilo

`crear_respuesta()` deja el borrador enganchado al hilo original, con las
cabeceras `In-Reply-To` y `References` del ultimo mensaje.

Insistir en un correo nuevo es empezar de cero: quien lo abre no ve el
historial, no encuentra el folio que ya se dio, y responde otra vez la
plantilla. Una respuesta en el hilo llega con todo lo anterior debajo.

## Cicatriz 1: dos clicks, dos borradores

El comentario del codigo decia "para no duplicarlo", pero nadie leia la nota
antes de crear. Ahora `borrador_existente()` comprueba en Gmail y devuelve el
mismo; y `crear_respuesta()` acepta un identificador para REESCRIBIR en vez de
crear otro. Corregir un correo antes de mandarlo es lo normal, y sin eso cada
correccion dejaba una copia mas.

## Cicatriz 2: el borrador que se dirigia a si mismo

Para saber a quien responder, `crear_respuesta()` miraba el ultimo mensaje del
hilo. Al REESCRIBIR un borrador, el ultimo mensaje del hilo pasa a ser ese
mismo borrador — que va DEL usuario. Asi que el destinatario se deducia de su
propio `From` y el correo quedaba dirigido a el mismo.

Se detecto con un escrito ya redactado, a un clic de mandarselo a su buzon. La
regla que quedo: **al leer un hilo, los borradores no cuentan**. El modulo de
seguimiento ya se protegia de esto; `crear_respuesta` no.

Corolario mas general, porque el mismo fallo aparecio dos veces el mismo dia en
sitios distintos: un borrador no lleva la etiqueta `SENT`, asi que cualquier
filtro que separe "lo mio" de "lo suyo" solo por `SENT` **cuenta los borradores
propios como si fueran respuestas ajenas**. Hay que excluir `DRAFT` siempre.

## Verificar leyendo, no confiando

Las comprobaciones se hacen releyendo las cabeceras desde Gmail, no dando por
buena la respuesta de la propia funcion que acaba de escribir. Es la version
correo de la regla de la casa: **codigo servido no es pagina pintada** —
[[sistema/panel-de-vacantes]].
""",
        ["[[sistema/seguimiento-de-candidaturas]]", "[[sistema/correos-en-frio]]",
         "[[01-wiki]]"],
        "Sistema", "Gmail: borradores y lectura",
    )

    # ------------------------------------------------------------------ 3 --
    nota(
        "sistema/procesos-que-no-pasan-por-el-correo",
        "Procesos que no pasan por el correo",
        "decision", "hecho",
        ctx("por que un proceso que entra por telefono tiene que caber en la base")
        + """
## El dia que la primera respuesta del sistema no existio

El 27 de agosto de 2026 el usuario recibio **dos llamadas** en el mismo dia, y
ninguna de las dos podia existir para el sistema:

1. El **071 del Centro IA**, preguntando por que no habia comenzado el curso.
   Explico su caso y quedaron en mandarselo en las siguientes horas. (No llego
   ese dia.)
2. **Red Ambiental** (Red Acero), convocandole a un **examen**.

Que fueran dos llamadas y no una no es un detalle: es lo que separa "la empresa
contesto a su candidatura" de "un tercero le hablo de una vacante". Ver mas
abajo, porque el sistema estuvo a punto de publicarlo sin comprobarlo.

El segundo importa mas de lo que parece: es la **primera vez que una candidatura
de este sistema avanza mas alla de `enviada`** por algo que no sea un rebote
automatico. El embudo llevaba parado desde el principio.

El panel seguia diciendo **"Con respuesta: 0"**.

> **Por que no dice "la primera respuesta del sistema" a secas.** Lo levanto el
> agente `jefe`: ya habia una candidatura con `respondida` --el rebote de un
> `mailer-daemon` el 24-ago-- y tres acuses de gestiones desde el 8 de julio.
> Dicho sin matizar, el titular contradice el propio historial del usuario.

## Como se supo que la empresa habia llamado: preguntando

El mismo `jefe` levanto una segunda objecion, y esa era mas grave. Arriba se
dice "llamada del 071" y "en esa misma llamada le hablaron de la vacante", asi
que dar por hecho que **Red Acero contesto a la candidatura de OCC** era una
inferencia: pudo ser el Centro IA canalizandole a esa vacante. Si hubiera sido
una sola llamada originada por ellos, `con_respuesta` volvia a 0 y el titular
del dia se caia entero.

Se le pregunto al usuario. **Fueron DOS llamadas distintas**: el 071 del Centro
IA por el curso, y Red Ambiental por separado. La empresa contacto por su
cuenta y el examen es de esta vacante. `con_respuesta = 1` y
`canal_respuesta = 'telefono'` son correctos.

Lo que merece quedarse no es el resultado, es el camino: **dos sesiones
distintas dieron por hecho lo mismo porque encajaba**, no porque nadie lo
hubiera comprobado. Encajar no es constar. Cuando una cifra depende de quien
hizo que, la unica fuente es preguntarselo a quien estuvo alli.

## Por que fallo, que no fue por un calculo

No hubo ningun numero mal sumado. El fallo estaba una capa mas abajo: la nota
[[perfil/procesos-en-marcha]] se construia con

```sql
WHERE hilo_gmail IS NOT NULL
```

es decir, **un proceso solo existia si habia pasado por Gmail**. Una respuesta
telefonica no es que saliera mal clasificada: no tenia donde ponerse. La nota
podia contar solo una parte del mundo y presentaba esa parte como el todo.

Es el patron que este proyecto ya conoce con otro nombre. En
[[sistema/deteccion-de-vacantes-fantasma]] una vacante sin fecha salia con
riesgo bajo, que es falsa tranquilidad y no ausencia de riesgo. Aqui es lo
mismo: **cero respuestas no significaba que nadie hubiera contestado, sino que
el sistema no sabia mirar por donde contestaron.**

## Que se hizo

Tres columnas en `candidaturas` (ver [[sistema/almacen-sqlite]]):

| Columna | Para que |
|---|---|
| `canal_respuesta` | por donde ENTRO la respuesta: correo, telefono, portal |
| `pendiente` | que espera el proceso AHORA, en una linea |
| `pendiente_fecha` | cuando toca |

`via` ya decia por donde SALIO la candidatura, y son cosas distintas: la de
Red Ambiental salio por el portal de OCC y contestaron por telefono. Con una
sola columna esa frase no se puede escribir.

Se anadio ademas el estado `pendiente-accion`, que
[[sistema/seguimiento-de-candidaturas]] **no pisa**: como `entrevista` u
`oferta`, lo pone el usuario. Una heuristica no manda sobre un juicio humano.

## Los dos efectos secundarios que hubo que atar

- **`emparejar()` excluye ahora `via='telefono'`.** Busca en Enviados el correo
  cuyo asunto se parece al de la candidatura; sin la exclusion le habria pegado
  un hilo de Gmail a una llamada, y a partir de ahi el sistema contaria dias de
  silencio de un correo que nunca se mando. Un ancla equivocada es peor que
  ninguna: no da error.
- **`rendimiento()` cuenta `telefono` como su propio canal.** El `CASE` era
  binario --portal o correo-- asi que cualquier via nueva caia en el cajon de
  "correo" sin avisar. Hoy solo hay gestiones por telefono y el SQL ya las
  excluye, pero el dia que entre una candidatura por ahi habria inflado la tasa
  del correo con algo que nunca paso por Gmail.

## Donde se ve

En **★ Plan de hoy**, arriba del todo, bajo el rotulo "Te espera", antes que la
cola. Un examen con fecha no puede quedar por debajo de un hilo que lleva 28
dias callado, y ordenar por dias de silencio hacia justo eso.

## La leccion, en una linea

Cuando una cifra dice cero, la primera pregunta no es si esta bien sumada: es
si lo que cuenta **cabe** en la tabla.
""",
        ["[[sistema/seguimiento-de-candidaturas]]", "[[perfil/procesos-en-marcha]]",
         "[[sistema/almacen-sqlite]]", "[[sistema/deteccion-de-vacantes-fantasma]]",
         "[[01-wiki]]"],
        "Sistema", "Procesos que no pasan por el correo",
    )

    # ------------------------------------------------------------------ 4 --
    nota(
        "perfil/procesos-en-marcha",
        "Procesos en marcha",
        "guia", "en-progreso",
        ctx("los procesos del usuario que siguen vivos y esperan algo")
        + _cuerpo_procesos(),
        ["[[sistema/seguimiento-de-candidaturas]]", "[[perfil/perfil-del-candidato]]",
         "[[sistema/procesos-que-no-pasan-por-el-correo]]", "[[01-wiki]]"],
        "Perfil", "Procesos en marcha",
    )


def _corto(texto: str | None, tope: int) -> str:
    """Recorta por palabra entera y avisa con puntos suspensivos.

    Cortar a lo bruto daba "Centro IA (071): curso por i", que no se lee como
    un texto largo sino como un dato roto -- y un dato que parece roto hace
    dudar de la tabla entera, aunque el numero de al lado este bien.
    """
    texto = (texto or "").strip()
    if len(texto) <= tope:
        return texto
    recortado = texto[:tope].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return (recortado or texto[:tope]) + "..."


def _cuerpo_procesos() -> str:
    """La tabla sale de la BASE, no de aqui.

    Una nota de estado escrita a mano miente a las dos semanas y nadie se
    entera. Generandola desde `candidaturas` se corrige sola en cada corrida,
    y si la base no tiene nada, lo dice en vez de mostrar datos viejos.

    EL FILTRO QUE FALTABA (27-ago-2026). Esta consulta decia
    `WHERE hilo_gmail IS NOT NULL`, es decir: un proceso solo existia si habia
    pasado por Gmail. Ese dia el usuario recibio una llamada del 071 con DOS
    procesos dentro --el curso del Centro IA y el examen de Red Ambiental-- y
    ninguno tenia donde vivir. El segundo era la PRIMERA respuesta que recibia
    una candidatura de este sistema, y la nota seguia sin mencionarlo.

    No era un error de calculo: era una nota que solo podia contar una parte
    del mundo y presentaba esa parte como el todo. Ahora entra cualquier
    proceso vivo, tenga hilo de correo o no.
    """
    from almacen import conexion

    with conexion() as con:
        filas = [dict(r) for r in con.execute("""
            SELECT asunto, estado, enviada, respondida, dias_silencio, notas,
                   via, canal_respuesta, pendiente, pendiente_fecha
            FROM candidaturas
            WHERE hilo_gmail IS NOT NULL
               OR estado = 'pendiente-accion'
               OR via = 'telefono'
            ORDER BY (dias_silencio IS NULL), dias_silencio DESC""")]

    if not filas:
        return """
## Ahora mismo no hay ninguno

No hay ningun proceso vivo en la base: ni hilo de correo anclado, ni nada
pendiente por otra via. En cuanto se envie un correo desde el Gmail del usuario, [[sistema/seguimiento-de-candidaturas]] lo detecta solo y esta
tabla se rellena en la siguiente corrida.
"""

    rotulo = {"enviada": "esperando", "acuse": "contestaron",
              "silencio": "sin respuesta", "rebote": "DEVUELTO",
              "pendiente-accion": "TE TOCA A TI"}

    lineas = []

    # Lo que espera un gesto del usuario va PRIMERO y en su propia tabla. Si
    # se mezcla con los hilos ordenados por dias de silencio, un examen con
    # fecha acaba por debajo de un correo que lleva 28 dias callado, que es
    # exactamente el orden equivocado.
    acciones = [f for f in filas if f["estado"] == "pendiente-accion"]
    if acciones:
        acciones.sort(key=lambda f: (f["pendiente_fecha"] is None,
                                     f["pendiente_fecha"] or ""))
        lineas += ["", "## Te toca a ti", "",
                   "| Que hay que hacer | Cuando | De donde salio |",
                   "|---|---|---|"]
        for f in acciones:
            origen = ("una llamada" if f["canal_respuesta"] == "telefono"
                      else (f["canal_respuesta"] or f["via"] or "-"))
            lineas.append(
                f"| {(f['pendiente'] or 'sin definir')[:52]} "
                f"| {f['pendiente_fecha'] or 'sin fecha'} "
                f"| {_corto(f['asunto'], 44)}, por {origen} |")

    esperando = [f for f in filas if f["estado"] != "pendiente-accion"]
    lineas += ["", "## Que esta esperando respuesta", "",
               "| Asunto | Estado | Enviada | Dias callado |", "|---|---|---|---|"]
    if not esperando:
        lineas.append("| (ninguno) | - | - | - |")
    for f in esperando:
        dias = "-" if f["dias_silencio"] is None else str(f["dias_silencio"])
        lineas.append(
            f"| {(f['asunto'] or '(sin asunto)')[:52]} "
            f"| {rotulo.get(f['estado'], f['estado'])} "
            f"| {f['enviada'] or '-'} | {dias} |")

    insistir = [f for f in esperando if (f["dias_silencio"] or 0) >= 7]
    lineas += ["", "## Lectura", "",
               f"{len(filas)} procesos vivos: {len(acciones)} esperan un gesto tuyo "
               f"y {len(esperando)} esperan respuesta ajena, de los cuales "
               f"{len(insistir)} llevan 7 dias o mas callados.", "",
               "No todos entraron por correo. Contarlos solo por Gmail era el "
               "fallo del 27-ago-2026 — ver "
               "[[sistema/procesos-que-no-pasan-por-el-correo]].", ""]
    if insistir:
        lineas.append("Los que tocaria insistir:")
        lineas += [f"- **{(f['asunto'] or '')[:60]}** — {f['dias_silencio']} dias"
                   for f in insistir]
        lineas.append("")
    lineas += [
        "## Que NO vive en esta nota", "",
        "Folios, CURP y numeros de expediente **no se copian aqui**. Viven en el",
        "correo, que ya es su sitio, y la boveda esta pensada para ser portatil y",
        "algun dia publica — ver [[reglas-de-la-boveda]]. Duplicar un",
        "identificador personal en un markdown que se copia entre maquinas es",
        "crear un sitio mas donde se puede filtrar, sin ganar nada.", ""]
    return "\n".join(lineas)

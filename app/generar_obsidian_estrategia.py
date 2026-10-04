"""
Notas del giro estrategico: de listar vacantes a producir candidaturas.

Por que en un archivo aparte. `generar_obsidian.py` ya son 52 KB y documenta
el MOTOR (recoleccion, clasificacion, verificacion). Esto documenta la
ESTRATEGIA, que es otra cosa y cambia por otras razones: el motor se toca
cuando falla una fuente, esto cuando cambia como se busca trabajo.
"""
from __future__ import annotations

from generar_obsidian import ctx, nota


def notas_estrategia(est: dict | None = None) -> None:
    """Las cuatro notas del giro del 22 de agosto de 2026."""

    # ------------------------------------------------------------------ 1 --
    nota(
        "sistema/el-giro-de-listar-a-postular",
        "El giro: de listar vacantes a producir candidaturas",
        "decision", "hecho",
        ctx("por que el sistema dejo de ser un buscador")
        + """
## El dato que lo obligo

Despues de dias afinando la recoleccion, el sistema recomendaba **2.681
vacantes** y el usuario habia postulado a **cero**.

No era un fallo de la herramienta: era un fallo de diseño. Se habia
optimizado la ENTRADA (encontrar anuncios) cuando el atasco estaba en la
SALIDA (postular). Una lista de 2.681 elementos no ayuda a nadie; es una
forma elegante de no empezar nunca, porque nadie abre eso y decide a cual
escribirle hoy.

## El segundo dato, que explico por que era generico

Al mirar QUIEN publica en Monterrey, las dos "empresas" con mas anuncios
resultaron ser:

| Anuncios | "Empresa" |
|---|---|
| 67 | Recomendada |
| 49 | Importante empresa del sector |

116 anuncios que ni siquiera dicen quien contrata. El sistema estaba jugando
en el canal donde un candidato sin experiencia tiene MENOS ventaja: bolsas
publicas, cientos de curriculums por vacante, y sin saber a quien le escribe.

## Que cambio

1. **La unidad de analisis**: de vacantes a empresas —
   [[sistema/empresas-y-mercado-oculto]].
2. **La salida**: una cola diaria de tres candidaturas con el correo ya
   escrito — [[sistema/cola-de-candidaturas]].
3. **El canal**: se abrio el correo directo a personas concretas —
   [[sistema/correos-en-frio]].

## La metrica, desde entonces

**Candidaturas enviadas.** No vacantes recolectadas, no notas generadas. Una
mejora que no acerque una candidatura es decoracion.
""",
        ["[[sistema/empresas-y-mercado-oculto]]", "[[sistema/cola-de-candidaturas]]",
         "[[sistema/correos-en-frio]]", "[[01-wiki]]"],
        "Decisiones de diseño", "El giro: de listar a postular",
    )

    # ------------------------------------------------------------------ 2 --
    nota(
        "sistema/empresas-y-mercado-oculto",
        "Empresas objetivo y mercado oculto",
        "componente", "hecho",
        ctx("como el sistema decide a que empresas apuntar, publiquen o no")
        + """
## La idea

Una empresa con operacion de seguridad o datos en Monterrey sigue siendo un
objetivo **aunque hoy no publique nada**, porque la mayoria de las practicas
se dan sin anuncio de por medio. Eso es el mercado oculto, y es donde alguien
sin experiencia compite contra casi nadie en vez de contra cientos.

`app/empresas.py` construye el mapa desde las vacantes ya recolectadas:
1.611 empresas, de las cuales **664 son objetivos reales en Monterrey**.

## Que hace que una empresa sea buen objetivo

La señal mas valiosa no es cuantas vacantes publica —esa suele ser una
agencia publicando para terceros— sino:

- **que YA contrate practicantes**: significa que la puerta existe y esta
  abierta, no que haya que convencer a nadie de hacer una excepcion;
- que tenga operacion tecnica propia (sus anuncios nombran SIEM, SOC, AWS…);
- que este en el area metropolitana.

## Las tres vias, y por que no son dos

| Via | Cuando | Que hacer |
|---|---|---|
| `programa-formal` | Tiene convocatoria de becarios con fechas (Cemex, Deloitte, Scotiabank, Accenture) | Postular por su portal |
| `vacante-publicada` | Hay anuncio abierto | Postular, y opcionalmente reforzar |
| `espontanea` | Ni programa ni anuncio | **Correo directo**: es la unica via |

Esta distincion corrige una intuicion que el sistema tenia mal. Donde existe
un programa formal, **escribirle en frio al responsable tecnico NO salta la
fila y puede irritar a quien decide**. El correo directo brilla justo donde
no hay proceso que competir.

## Dos correcciones que el mapa no podia ver solo

Un mapa hecho de anuncios tiene dos puntos ciegos, documentados en
`app/datos_empresas.py`:

- **Sobrevalora la presencia local.** Corning salia con 100 puntos, pero su
  operacion real de TI esta en Reynosa; lo de Apodaca es una planta. Ajustado.
- **No ve a quien no publica.** Scitum —la empresa de ciberseguridad de
  Telmex, con SOC en Monterrey y becas de ciberinteligencia ya abiertas
  antes— no aparecia porque no publica en nuestras fuentes. Justo las mejores
  puertas del mercado oculto son invisibles para un mapa de anuncios.

## Uso

```bash
python app/empresas.py --top 20
```
""",
        ["[[sistema/el-giro-de-listar-a-postular]]", "[[sistema/correos-en-frio]]",
         "[[01-wiki]]"],
        "Sistema", "Empresas objetivo y mercado oculto",
    )

    # ------------------------------------------------------------------ 3 --
    nota(
        "sistema/cola-de-candidaturas",
        "La cola del dia: tres candidaturas listas",
        "feature", "hecho",
        ctx("la pieza que convierte el catalogo en accion")
        + """
## Que hace

Cada dia elige **tres** candidaturas —no dos mil seiscientas—, escribe el
correo de cada una y deja solo dos acciones: enviar o descartar. Vive en la
pestaña «★ Plan de hoy» del panel y en `app/cola.py`.

Tres es el numero a proposito: suficiente para avanzar de verdad, pocas para
que no se posponga.

## Las reglas al elegir, y por que existen

- **Nunca repite empresa en la misma semana.** Dos correos en tres dias a la
  misma compañia no duplican las opciones: las queman.
- **Nunca repite vacante ya enviada o descartada.** Un borrador NO bloquea:
  el panel registra uno cada vez que muestra la cola, y si eso excluyera la
  vacante, cada recarga propondria tres distintas — la cola pareceria una
  ruleta en vez de un plan.
- **Mezcla las dos vias**: dos por portal y una en frio. La via en frio tiene
  menos competencia pero tarda; la publicada es inmediata pero compite con
  cientos. Hacer solo una es apostar todo a un canal.
- **Prioriza lo que caduca.** Una vacante de hace tres dias vale mas que una
  de hace tres meses aunque puntue algo menos: la segunda probablemente ya
  tiene finalistas.

## Lo que se guarda despues

La tabla `candidaturas` registra que se mando, a quien, cuando y si
contestaron. Sirve para dos cosas que ninguna lista puede dar: no repetirse
ante la misma empresa, y **saber que funciona**. Sin ese registro, "manda mas
correos" es un consejo a ciegas; con el se sabe si contestan mas las cartas
en frio o las postulaciones por portal, y se apuesta al que gane.

## Uso

```bash
python app/cola.py --preparar        # la cola de hoy, con correos
python app/cola.py --enviada ID      # marcar una como enviada
```
""",
        ["[[sistema/el-giro-de-listar-a-postular]]", "[[sistema/panel-de-vacantes]]",
         "[[01-wiki]]"],
        "Sistema", "La cola del dia",
    )

    # ------------------------------------------------------------------ 4 --
    nota(
        "sistema/correos-en-frio",
        "Correos en frio: escribirle a una persona",
        "componente", "hecho",
        ctx("como se escribe a alguien que no espera tu correo")
        + """
## En que se diferencia de una postulacion

`generador_correos.py` responde a un anuncio: el lector espera ese correo.
`correos_frios.py` escribe a alguien que **no espera nada**, y eso cambia
todas las reglas:

- **Corto o muerto.** Un director de TI decide en diez segundos si sigue
  leyendo. Maximo ~120 palabras; cada frase que no aporta, resta.
- **El asunto no puede oler a spam.** Nada de "Oportunidad" ni mayusculas.
- **Un solo pedido, y pequeño.** No se pide trabajo: se piden 15 minutos o
  una referencia. A un desconocido se le pide algo que pueda dar sin pensar.
- **Por que ELLOS, demostrado.** La primera linea nombra algo de la empresa
  —su SOC, su stack— que solo sabe quien la miro de verdad. El dato sale de
  la tabla `empresas`, deducido de sus propios anuncios.

## El hallazgo que ordena a quien escribir

Se busco en 11 empresas y **no aparecio el nombre de un solo reclutador** en
ninguna fuente publica. Aparecieron **nueve responsables tecnicos**. RH es un
buzon sin cara; el responsable tecnico tiene ponencia, biografia y
entrevista. A un buzon no se le puede escribir algo que solo le sirva a el; a
alguien cuya charla viste, si.

## Las dos reglas innegociables

1. **Ningun hecho fuera de `perfil.py`** (incluido `LOGROS`). Un dato
   inventado no se corrige despues: quema al candidato con esa empresa para
   siempre.
2. **Solo informacion profesional publicada** para los contactos. Prohibido
   el OSINT de brechas de datos: es un problema legal bajo la LFPDPPP y la
   peor carta de presentacion imaginable para quien quiere que lo contraten
   en seguridad.

## Verificado frente a inferido

Ningun correo individual de la base esta confirmado: son el patron de la
empresa aplicado al nombre. El campo `confianza` lo dice y **el aviso viaja
con el borrador**, porque presentar un correo deducido como confirmado haria
que el usuario escriba a una direccion inexistente y espere una respuesta que
nunca salio de su bandeja.

## Uso

```bash
python app/correos_frios.py --empresa Sigma
```
""",
        ["[[sistema/empresas-y-mercado-oculto]]", "[[guias/correos-de-postulacion]]",
         "[[01-wiki]]"],
        "Sistema", "Correos en frio",
    )

    # ------------------------------------------------------------------ 5 --
    nota(
        "sistema/formacion-gratuita",
        "Formacion gratuita para cerrar brechas",
        "feature", "hecho",
        ctx("como se eligen los cursos que de verdad abren puertas")
        + """
## Por que vive en el mismo sistema que las vacantes

El panel ya sabe QUE piden los anuncios. Midiendo la base salio que **la nube
(AWS, Azure, GCP) aparece en el 21,6% de las vacantes de practicas y junior**
y es el mayor hueco del CV del usuario. Un curso no es un adorno: es la
pieza que convierte una vacante inalcanzable en alcanzable.

Por eso los cursos se puntuan contra la MISMA base de vacantes, no contra una
idea abstracta de lo que conviene aprender. Los pesos salen de contar:

| Area | Peso | Motivo |
|---|---|---|
| Nube | 30 | 21,6% de las vacantes junior |
| IA | 22 | |
| Ciberseguridad | 20 | |
| Redes | 14 | |

Y un curso que repite lo que ya sabe (ISO 27001, Python) **baja de puesto**:
le quita tiempo para cerrar lo que le falta.

## La distincion que gobierna el modulo

"Gratis" no es un si/no. Son tres cosas distintas, y confundirlas es el error
mas caro para alguien que no puede pagar:

| Valor | Significa |
|---|---|
| `total` | Curso y credencial sin coste |
| `examen-pago` | El material es gratis, el examen cuesta (y el precio viaja pegado) |
| `beca` | Gratis solo si le aprueban la convocatoria |

Esto se calibro con un empate que delato el fallo: AZ-900 (examen de 99 USD)
y OCI Foundations (examen gratis) sacaban los mismos puntos, porque lo que
AZ-900 perdia en gratuidad lo recuperaba por marca. Para el usuario eso es
falso: **99 dolares no son un matiz, son un muro**. Ahora la gratuidad total
gana siempre a la marca.

## El hallazgo

**Oracle regala curso Y examen.** AWS cobra 100 USD, Microsoft 99, Cisco 125,
Oracle 0. Es la unica certificacion de nube de fabricante realmente gratuita,
y desde agosto de 2026 tambien en nivel Associate.

## Verificacion

Cada URL se comprueba de verdad. Regla heredada del verificador de vacantes:
**un 403 significa "el sitio no me deja mirar", nunca "el curso no existe"** —
los sitios de gobierno y Oracle bloquean bots y funcionan en navegador.

## Uso

```bash
python app/cursos.py --verificar
```
""",
        ["[[guias/mejorar-el-cv]]", "[[sistema/panel-de-vacantes]]", "[[01-wiki]]"],
        "Sistema", "Formacion gratuita",
    )

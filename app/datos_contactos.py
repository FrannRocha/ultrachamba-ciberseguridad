"""
Personas a quien escribir (contactos de EJEMPLO).

PLANTILLA. Las entradas de abajo son ficticias y solo muestran la estructura:
dominios `example.com`, `correo_origen` "inferido" y `confianza`
"no-verificado". Sustituyelas por TUS contactos reales.

Reglas que conviene mantener:
- Ningun correo inferido por patron es un correo confirmado: puede rebotar. El
  campo `correo_origen` lo dice y el panel debe enseñarlo, para no escribir a
  una direccion inexistente creyendo que se acerto.
- Usa solo fuentes profesionales publicas (perfiles oficiales, ponencias, notas
  de prensa). No uses corredores de datos: son revendedores de informacion
  personal, no fuentes.
- No incluyas datos personales de terceros sin una base legitima para ello, y
  nunca los subas a un repositorio publico.

Cada entrada lleva `empresa` tal como aparece en la tabla `empresas`, para
poder enlazarla. Si el nombre no coincide, la fila se queda sin enlazar y se
reporta en vez de inventar la union.
"""
from __future__ import annotations

CONTACTOS = [
    {
        "empresa": "EJEMPLO — Empresa Uno", "nombre": "EJEMPLO — Nombre Apellido",
        "puesto": "Director de Tecnologias de la Informacion",
        "correo": "contacto@example.com",
        "correo_origen": "inferido-por-patron", "confianza": "no-verificado",
        "fuente": "EJEMPLO — de donde salio (fuente publica)",
        "notas": "EJEMPLO. Reemplaza por un contacto real. Un correo inferido "
                 "por patron puede rebotar: marcalo como no verificado.",
    },
    {
        "empresa": "EJEMPLO — Empresa Dos", "nombre": "EJEMPLO — Otra Persona",
        "puesto": "Coordinacion de Seguridad",
        "correo": "", "correo_origen": "", "confianza": "no-verificado",
        "fuente": "EJEMPLO — ponencia o perfil oficial",
        "notas": "EJEMPLO sin correo: hay que buscarlo o escribir por el sitio.",
    },
]

# Puertas institucionales con correo PUBLICADO y abierto (EJEMPLO). Valen mas
# que adivinar una direccion, porque el correo es publico.
PUERTAS = [
    {
        "empresa": "EJEMPLO — Cluster o Comunidad TI",
        "nombre": "EJEMPLO — Direccion General", "puesto": "Direccion General",
        "correo": "info@example.org", "correo_origen": "publicado",
        "confianza": "no-verificado", "fuente": "EJEMPLO — sitio oficial",
        "notas": "EJEMPLO. Un cluster o comunidad puede llegar a muchas puertas "
                 "a la vez; usa su correo publicado.",
    },
]

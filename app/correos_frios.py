"""
Correos en frio: escribirle a una persona, no postular a una vacante.

En que se diferencia del generador de postulaciones. `generador_correos.py`
responde a un anuncio: el lector espera ese correo. Aqui NADIE lo espera, y
eso cambia todas las reglas:

  - **Corto o muerto.** Un director de TI decide en diez segundos si sigue
    leyendo. Maximo ~120 palabras de cuerpo; cada frase que no aporta, resta.
  - **El asunto no puede parecer spam.** Nada de "Oportunidad", "Candidato
    disponible" ni mayusculas. Funciona lo concreto: que es y que pide.
  - **Un solo pedido, y pequeño.** No se pide trabajo: se piden 15 minutos o
    una referencia. A un desconocido no se le pide un contrato; se le pide
    algo que pueda dar sin pensarlo dos veces.
  - **Por que ELLOS, demostrado.** La primera linea tiene que probar que no es
    un correo en masa: nombra algo de la empresa (su SOC, su stack, su
    programa) que solo sabe quien la miro de verdad. El dato sale de la tabla
    `empresas`, que lo dedujo de sus propios anuncios.

Y la regla que manda sobre todas: **ningun hecho que no este en `perfil.py`**.
Un dato inventado no se corrige despues: quema al candidato con esa empresa
para siempre.

Uso:
    python correos_frios.py                  # borradores para los objetivos con contacto
    python correos_frios.py --empresa Sigma
"""
from __future__ import annotations

import argparse
import json

from almacen import conexion
from perfil import CANDIDATO, LOGROS

# ---------------------------------------------------------------------------
# Angulo por tipo de destinatario. No es lo mismo escribirle al director de TI
# (decide contrataciones), a la coordinadora de un laboratorio (busca manos
# utiles ya), o a un cluster (presenta, no contrata).
# ---------------------------------------------------------------------------


def _angulo(empresa: dict, contacto: dict) -> tuple[str, list[str]]:
    """Elige que historia contar segun quien lee y que hace su empresa."""
    puesto = (contacto.get("puesto") or "").lower()
    sector = (empresa.get("sector") or "").lower()
    stack = (empresa.get("stack") or "").lower()

    if "cluster" in sector:
        return ("presentacion", LOGROS["ciberseguridad"][:1] + LOGROS["ia"][:1])
    if "lab" in puesto or "scilabs" in puesto.lower() or "investigacion" in puesto:
        # A un laboratorio de amenazas le importa que produzcas algo util
        # pronto: el detector de LLM es el mejor ejemplo demostrable.
        return ("laboratorio", LOGROS["ia"] + LOGROS["ciberseguridad"][:1])
    if "ciberseguridad" in sector or "soc" in stack or "siem" in stack:
        return ("seguridad", LOGROS["ciberseguridad"][:2] + LOGROS["ia"][:1])
    if "datos" in puesto or "ia" in sector:
        return ("ia", LOGROS["ia"] + LOGROS["ti"][:1])
    return ("general", LOGROS["ciberseguridad"][:1] + LOGROS["ia"][:1] + LOGROS["ti"][:1])


def _gancho(empresa: dict, angulo: str) -> str:
    """La primera linea: la prueba de que este correo no es en masa."""
    nombre = empresa.get("nombre_limpio") or empresa.get("nombre") or "su empresa"
    stack = [s for s in (empresa.get("stack") or "").split(",") if s][:3]
    n_ciber = empresa.get("vacantes_ciber") or 0

    if angulo == "presentacion":
        return (f"Sigo el trabajo de {nombre} conectando a las empresas de "
                "tecnologia de Nuevo Leon, y este año participe en Hola IA.")
    if angulo == "laboratorio":
        return (f"Sigo lo que publica {nombre} sobre investigacion de amenazas, "
                "y es exactamente el trabajo que quiero aprender a hacer bien.")
    if n_ciber and stack:
        return (f"Vi que {nombre} esta creciendo su equipo de seguridad "
                f"(sus vacantes nombran {', '.join(stack)}), y por eso le "
                "escribo a usted y no a un buzon generico.")
    if n_ciber:
        return (f"Vi que {nombre} tiene operacion de seguridad propia en "
                "Monterrey, y por eso le escribo a usted directamente.")
    return (f"Investigue que empresas de Monterrey tienen operacion tecnica "
            f"real, y {nombre} esta en mi lista corta.")


def generar_frio(empresa: dict, contacto: dict) -> dict:
    """Devuelve {'asunto', 'cuerpo', 'avisos'} para un contacto concreto."""
    angulo, logros = _angulo(empresa, contacto)
    nombre_e = empresa.get("nombre_limpio") or empresa.get("nombre") or ""
    # Solo el nombre de pila: "Estimado/a Nombre Apellido Apellido" es la firma
    # de un correo en masa, que es exactamente lo que este correo debe no
    # parecer. "Estimado Nombre" es lo normal en el español de negocios
    # mexicano, y ademas evita adivinar el genero por el apellido.
    pila = (contacto.get("nombre") or "").strip().split(" ")[0]
    trato = f"Estimado/a {pila}" if pila else "Estimado equipo"

    # Un solo pedido, pequeño. A un cluster se le pide difusion; a los demas,
    # quince minutos o que digan a quien si.
    if angulo == "presentacion":
        pedido = ("¿Habria forma de que mi perfil llegue a las empresas del "
                  "cluster que reciban practicantes de seguridad o IA? Adjunto "
                  "CV; con una linea suya me basta.")
    else:
        pedido = ("¿Tendria 15 minutos en las proximas semanas para "
                  "platicarme como se entra a un equipo como el suyo? Y si "
                  "usted no es la persona indicada, le agradeceria que me "
                  "diga quien si.")

    hechos = "; ".join(logros[:2])
    cuerpo = f"""{trato}:

{_gancho(empresa, angulo)}

Soy {CANDIDATO['grado']} y busco practicas en ciberseguridad o IA. Sin experiencia formal todavia, pero con trabajo que se puede revisar: {hechos}.

{pedido}

Saludos,
{CANDIDATO['nombre']}
{CANDIDATO['linkedin']}
{CANDIDATO['github']} · {CANDIDATO['telefono']}"""

    asunto = {
        "presentacion": "Estudiante de seguridad — busco llegar a las empresas del cluster",
        "laboratorio": "Perfil de seguridad + IA — ¿15 minutos?",
        "seguridad": f"Estudiante de seguridad — pregunta breve sobre {nombre_e}",
        "ia": "Estudiante de seguridad + IA — pregunta breve",
        "general": f"Estudiante de seguridad — pregunta breve sobre practicas en {nombre_e}",
    }[angulo]

    avisos = []
    if (contacto.get("correo_origen") or "") == "inferido-por-patron":
        avisos.append(
            "EL CORREO ES DEDUCIDO POR PATRON Y PUEDE REBOTAR. Si rebota, no "
            "reintentar variantes a ciegas: escribir por LinkedIn al perfil de "
            f"{contacto.get('nombre')} o por el formulario del sitio.")
    if not contacto.get("correo"):
        avisos.append("Sin correo: enviar por LinkedIn o el formulario del sitio.")
    if (contacto.get("confianza") or "") == "probable-caduco":
        avisos.append("El dato del puesto es viejo: CONFIRMAR que sigue en el "
                      "cargo antes de enviar, o el correo llega a la persona "
                      "equivocada y quema el intento.")
    if contacto.get("notas"):
        avisos.append(f"Contexto: {contacto['notas']}")

    return {"asunto": asunto, "cuerpo": cuerpo, "angulo": angulo,
            "avisos": avisos, "destinatario": contacto.get("correo") or "(sin correo)"}


def para_empresa(nombre: str) -> list[dict]:
    """Borradores para todos los contactos de una empresa."""
    with conexion() as con:
        filas = con.execute("""
            SELECT c.*, e.nombre AS e_nombre, e.nombre_limpio, e.sector,
                   e.stack, e.vacantes_ciber, e.via
            FROM contactos c JOIN empresas e ON e.id = c.empresa_id
            WHERE e.nombre LIKE ? OR e.nombre_limpio LIKE ?
            ORDER BY CASE c.confianza WHEN 'verificado' THEN 0
                     WHEN 'inferido' THEN 1 ELSE 2 END""",
            (f"%{nombre}%", f"%{nombre}%")).fetchall()
    salida = []
    for f in filas:
        d = dict(f)
        empresa = {k: d.get(k) for k in
                   ("nombre_limpio", "sector", "stack", "vacantes_ciber", "via")}
        empresa["nombre"] = d["e_nombre"]
        salida.append({**generar_frio(empresa, d), "contacto": d.get("nombre"),
                       "puesto": d.get("puesto"), "empresa": empresa["nombre_limpio"]})
    return salida


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--empresa", default=None)
    args = p.parse_args()

    if args.empresa:
        borradores = para_empresa(args.empresa)
    else:
        with conexion() as con:
            nombres = [r["nombre_limpio"] for r in con.execute("""
                SELECT DISTINCT e.nombre_limpio FROM contactos c
                JOIN empresas e ON e.id = c.empresa_id
                WHERE e.via != 'programa-formal' ORDER BY e.score DESC LIMIT 4""")]
        borradores = [b for n in nombres for b in para_empresa(n)[:1]]

    for b in borradores:
        print("=" * 72)
        print(f"PARA:    {b['contacto']} ({b['puesto']})")
        print(f"CORREO:  {b['destinatario']}")
        print(f"ASUNTO:  {b['asunto']}")
        print("-" * 72)
        print(b["cuerpo"])
        if b["avisos"]:
            print("-" * 72)
            for a in b["avisos"]:
                print(f"  !! {a}")
        print()

"""
Formacion gratuita que le sirve al usuario para conseguir las practicas.

Por que esto vive en el mismo sistema que las vacantes. El panel ya sabe QUE
piden los anuncios; midiendo la base salio que la nube (AWS, Azure, GCP)
aparece en el 21,6% de las vacantes de practicas y junior y es el mayor hueco
de su CV. Un curso no es un adorno: es la pieza que convierte una vacante
inalcanzable en alcanzable. Por eso se puntuan contra la MISMA base de
vacantes, no contra una idea abstracta de lo que conviene aprender.

La distincion que gobierna el modulo. "Gratis" no es un si/no:

    total        -> curso y credencial sin coste
    examen-pago  -> el material es gratis, el examen cuesta dinero
    beca         -> gratis solo si le aprueban una convocatoria

El usuario no puede pagar. Presentar un curso de 'examen-pago' como gratuito
seria mentirle, asi que el coste del examen viaja siempre junto al curso y el
panel lo enseña.

Uso:
    python cursos.py              # puntua y muestra los mejores
    python cursos.py --verificar  # comprueba que las URLs siguen vivas
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date, datetime

from almacen import conexion
from nucleo import ahora_iso, normalizar, tiene_termino

# Pesos de las areas. Salen de contar la base, no de opinar: sobre las 656
# vacantes de practicas y junior con descripcion real, la nube aparece en el
# 21,6%, Python en el 22,6% y las herramientas clasicas de seguridad (SIEM,
# ISO 27001) por debajo del 3%. Un curso de nube abre mas puertas que uno de
# SIEM aunque suene menos a ciberseguridad.
PESO_AREA = {
    "nube": 30,
    "ia": 22,
    "ciberseguridad": 20,
    "redes": 14,
    "general": 6,
}

# Lo que ya tiene, segun `perfil.py`. Un curso que solo repite esto no le suma:
# le quita tiempo para cerrar lo que le falta.
def _ya_cubierto() -> list[str]:
    """Lo que TU perfil ya cubre: un curso sobre esto vale menos para ti.

    Sale de `perfil.COMPETENCIAS` (las que declaras con algun nivel) en vez de
    una lista fija: escrita a mano describiria el curriculum de otra persona y
    ordenaria los cursos por los huecos de esa persona, no por los tuyos.
    """
    try:
        from perfil import COMPETENCIAS
    except Exception:
        return []
    return [clave.lower() for clave, valor in COMPETENCIAS.items()
            if (valor[0] or "").lower() not in ("", "ninguno")]


YA_CUBIERTO = _ya_cubierto()

# Areas de hueco habituales en un perfil junior de ciberseguridad: un curso que
# toca esto vale mas que uno que no. Son categorias por defecto, no un
# diagnostico de nadie; lo que TU ya cubres sale de `YA_CUBIERTO`, que lee tu
# perfil. Ajusta estas listas si tu hueco es otro.
BRECHAS = {
    "nube": ["aws", "azure", "gcp", "google cloud", "cloud", "terraform",
             "kubernetes", "docker"],
    "ia": ["machine learning", "deep learning", "llm", "nlp", "mlops",
           "redes neuronales", "aprendizaje automatico"],
    "ofensiva": ["pentest*", "ethical hacking", "red team", "bug bounty",
                 "hacking etico"],
    "certificacion-reconocida": ["comptia", "security+", "ccna", "cyberops",
                                 "az-900", "sc-900", "aws certified",
                                 "cloud practitioner"],
}


def identificador(nombre: str, institucion: str) -> str:
    base = normalizar(f"{institucion}|{nombre}")
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]


def _dias_para_cerrar(cierra: str | None) -> int | None:
    if not cierra:
        return None
    try:
        d = datetime.strptime(str(cierra)[:10], "%Y-%m-%d").date()
        return (d - date.today()).days
    except ValueError:
        return None


def puntuar(c: dict) -> dict:
    """Puntua un curso por lo que le abre al usuario, no por prestigio."""
    texto = normalizar(" ".join(str(c.get(k) or "") for k in
                                ("nombre", "descripcion", "credencial", "por_que")))
    puntos = 0.0
    motivos: list[str] = []
    brechas: list[str] = []

    area = (c.get("area") or "general").lower()
    peso = PESO_AREA.get(area, 6)
    puntos += peso
    motivos.append(f"area {area}: {peso} puntos por lo que piden las vacantes de la base")

    for nombre_brecha, terminos in BRECHAS.items():
        if any(tiene_termino(texto, t) for t in terminos):
            brechas.append(nombre_brecha)
            puntos += 14
            motivos.append(f"cierra una brecha real de su CV: {nombre_brecha}")

    # Coste. Es lo primero que mira alguien que no puede pagar, asi que pesa
    # mas que ninguna otra cosa.
    #
    # Calibrado con un empate que delato el fallo: AZ-900 (examen de 99 USD) y
    # OCI Foundations (examen gratis) sacaban los mismos 76 puntos, porque lo
    # que AZ-900 perdia en gratuidad lo recuperaba por ser "certificacion
    # reconocida". Para el usuario eso es falso: 99 dolares no son un matiz, son
    # un muro. La gratuidad total tiene que ganar siempre a la marca.
    gratis = (c.get("gratis") or "").lower()
    if gratis == "total":
        puntos += 30
        motivos.append("gratis de verdad: curso y credencial sin coste")
    elif gratis == "examen-pago":
        # No suma nada: el material gratis ya se premia por otras vias, y el
        # examen de pago deja la credencial fuera de su alcance.
        motivos.append("OJO: el material es gratis pero el examen cuesta "
                       + (c.get("costo_examen") or "una cantidad sin confirmar"))
    elif gratis == "beca":
        puntos += 14
        motivos.append("gratis solo si le aprueban la beca o la convocatoria")

    # Una credencial verificable es lo que puede poner en el CV manana.
    if (c.get("credencial") or "").strip():
        # Una credencial que exige pagar el examen no es una credencial que
        # tenga: es una que podria tener si tuviera el dinero.
        if gratis == "examen-pago":
            puntos += 4
            motivos.append("la credencial existe pero esta detras del examen de pago: "
                           + c["credencial"])
        else:
            puntos += 12
            motivos.append("deja credencial demostrable: " + c["credencial"])
    else:
        motivos.append("no deja credencial: solo sirve por lo aprendido")

    # Presencial en Monterrey suma: hace red de contactos, que es como se
    # consiguen las practicas que nunca llegan a publicarse.
    if (c.get("modalidad") or "") == "presencial-mty":
        puntos += 8
        motivos.append("presencial en Monterrey: ademas de aprender, hace contactos")

    # Urgencia: una convocatoria que cierra pronto tiene que subir en la lista.
    dias = _dias_para_cerrar(c.get("cierra"))
    if (c.get("convocatoria") or "") == "cerrada":
        puntos -= 40
        motivos.append("la convocatoria ya cerro")
    elif dias is not None:
        if dias < 0:
            puntos -= 40
            motivos.append(f"el plazo vencio hace {abs(dias)} dias")
        elif dias <= 14:
            puntos += 15
            motivos.append(f"URGENTE: cierra en {dias} dias")
        elif dias <= 45:
            puntos += 8
            motivos.append(f"cierra en {dias} dias")

    # Repetir lo que ya sabe no le acerca a nada.
    repetidos = [t for t in YA_CUBIERTO if tiene_termino(texto, t)]
    if repetidos and not brechas:
        puntos -= 10
        motivos.append("repite lo que ya tiene (" + ", ".join(repetidos[:3])
                       + ") sin cubrir ningun hueco")

    if (c.get("idioma") or "").lower().startswith("ing"):
        motivos.append("en ingles: comprueba que tu nivel te alcanza; de paso lo practicas")

    return {**c,
            "score": round(max(0.0, min(100.0, puntos)), 1),
            "motivos": motivos,
            "brecha": ",".join(brechas)}


def guardar(cursos: list[dict]) -> int:
    """Guarda respetando lo que ya estuviera verificado."""
    ahora = ahora_iso()
    campos = ["id", "nombre", "institucion", "url", "area", "modalidad", "gratis",
              "costo_examen", "credencial", "convocatoria", "cierra", "duracion",
              "idioma", "descripcion", "por_que", "score", "motivos", "brecha"]
    with conexion() as con:
        for entrada in cursos:
            c = puntuar(entrada)
            c["id"] = c.get("id") or identificador(c["nombre"], c.get("institucion", ""))
            c["motivos"] = json.dumps(c.get("motivos") or [], ensure_ascii=False)
            valores = [c.get(k) for k in campos]
            marcas = ",".join("?" * len(campos))
            actualiza = ",".join(f"{k}=excluded.{k}" for k in campos if k != "id")
            con.execute(
                f"""INSERT INTO cursos ({",".join(campos)}, primera_vez, ultima_vez)
                    VALUES ({marcas}, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET {actualiza},
                        ultima_vez=excluded.ultima_vez""",
                valores + [ahora, ahora])
    return len(cursos)


# Señales de que una pagina de curso ya no admite inscripciones. Se buscan solo
# si la respuesta fue 200: si hubo error HTTP, manda el codigo.
CERRADO = re.compile(
    r"(convocatoria cerrada|inscripciones cerradas|registro cerrado|"
    r"ya no se admiten|cupo lleno|applications? (are )?closed|"
    r"registration (is )?closed|no longer available)", re.I)


def verificar(limite: int = 100) -> dict:
    """Comprueba que cada curso siga existiendo y admitiendo inscripcion.

    Misma regla que en las vacantes: **ante la duda no se marca como cerrado**.
    Un 403 significa que el sitio no deja mirar, no que el curso no exista.
    """
    import httpx

    cabeceras = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/126.0 Safari/537.36"),
                 "Accept-Language": "es-MX,es;q=0.9,en;q=0.8"}
    with conexion() as con:
        filas = [dict(r) for r in con.execute(
            "SELECT id, nombre, url FROM cursos WHERE url LIKE 'http%' LIMIT ?",
            (limite,))]

    resultados: list[tuple] = []
    cuenta = {"viva": 0, "cerrada": 0, "inaccesible": 0}
    with httpx.Client(follow_redirects=True, timeout=25, headers=cabeceras) as cli:
        for f in filas:
            try:
                r = cli.get(f["url"])
                if r.status_code in (404, 410):
                    estado = "cerrada"
                    detalle = f"la pagina ya no existe ({r.status_code})"
                elif r.status_code in (403, 429):
                    # Comprobado: MEXIA, Saberes, la EPC, Oracle, TryHackMe y
                    # Fortinet responden 403 o 429 a peticiones automatizadas y
                    # sin embargo abren perfectamente en un navegador. Un 403
                    # de un sitio de gobierno o de un fabricante NO es un
                    # enlace roto, y tratarlo como tal borraria del panel
                    # justo los programas gratuitos que mas le convienen.
                    estado = "inaccesible"
                    detalle = (f"el sitio bloqueo la lectura automatica ({r.status_code}); "
                               "casi seguro abre bien en el navegador")
                elif r.status_code != 200:
                    estado = "inaccesible"
                    detalle = f"respuesta inesperada ({r.status_code})"
                elif CERRADO.search(r.text[:80000]):
                    estado = "cerrada"
                    detalle = "la propia pagina dice que no admite inscripciones"
                else:
                    estado = "viva"
                    detalle = "la pagina responde y no dice estar cerrada"
                http = r.status_code
            except Exception as e:
                estado = "inaccesible"
                detalle = f"fallo la peticion: {type(e).__name__}"
                http = None
            cuenta[estado] = cuenta.get(estado, 0) + 1
            resultados.append((estado, http, ahora_iso(), detalle, f["id"]))

    with conexion() as con:
        con.executemany(
            "UPDATE cursos SET ver_estado=?, ver_http=?, ver_fecha=?, "
            "ver_detalle=? WHERE id=?", resultados)
    return cuenta


def consultar(area: str | None = None, solo_gratis: bool = False,
              solo_abiertos: bool = False) -> list[dict]:
    condiciones = ["(ver_estado IS NULL OR ver_estado != 'cerrada')"]
    args: list = []
    if area:
        condiciones.append("area = ?")
        args.append(area)
    if solo_gratis:
        condiciones.append("gratis = 'total'")
    if solo_abiertos:
        condiciones.append("(convocatoria != 'cerrada' OR convocatoria IS NULL)")
    with conexion() as con:
        filas = con.execute(
            f"SELECT * FROM cursos WHERE {' AND '.join(condiciones)} "
            "ORDER BY score DESC", args).fetchall()
    salida = []
    for f in filas:
        c = dict(f)
        try:
            c["motivos"] = json.loads(c.get("motivos") or "[]")
        except (TypeError, ValueError):
            c["motivos"] = []
        c["dias_para_cerrar"] = _dias_para_cerrar(c.get("cierra"))
        salida.append(c)
    return salida


def resumen() -> dict:
    with conexion() as con:
        fila = con.execute("""
            SELECT COUNT(*) total,
                   SUM(CASE WHEN gratis='total' THEN 1 ELSE 0 END) gratis_total,
                   SUM(CASE WHEN credencial IS NOT NULL AND credencial != ''
                            THEN 1 ELSE 0 END) con_credencial,
                   SUM(CASE WHEN brecha LIKE '%nube%' THEN 1 ELSE 0 END) de_nube
            FROM cursos WHERE ver_estado IS NULL OR ver_estado != 'cerrada'
            """).fetchone()
    return dict(fila)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--verificar", action="store_true",
                   help="comprueba que las URLs siguen vivas")
    args = p.parse_args()

    if args.verificar:
        print("verificacion:", verificar())

    lista = consultar()
    print(f"\n{len(lista)} cursos en la base\n")
    for c in lista[:20]:
        urgencia = ""
        if c["dias_para_cerrar"] is not None and 0 <= c["dias_para_cerrar"] <= 30:
            urgencia = f"  <- cierra en {c['dias_para_cerrar']} dias"
        print(f"  {c['score']:5.1f} | {(c['area'] or ''):14} | {c['nombre'][:44]:44} "
              f"| {(c['institucion'] or '')[:20]:20}{urgencia}")

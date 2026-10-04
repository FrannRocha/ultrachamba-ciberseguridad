"""
Exporta la boveda y el codigo del proyecto a texto plano para NotebookLM.

Para que sirve. La boveda tiene 97 notas y el codigo 38 modulos. Una sesion
nueva no puede leerlo todo, y aunque pudiera, gastaria el contexto entero en
eso. Subido a NotebookLM se le puede preguntar "por que se decidio X" o "que
hace el modulo Y" y responde **citando la nota o el archivo concreto**.

Complementa al panel y a la boveda; no los sustituye. La boveda sigue siendo
la fuente de verdad y esto es una copia de solo lectura para consultar.

Datos personales. El telefono, el correo y una CURP pueden aparecer en el
perfil o en las notas. Aqui se enmascaran antes de exportar: no aportan nada a
ninguna pregunta que se le vaya a hacer al cuaderno, y evitan dejarlos en un
servicio externo. Todo lo demas se exporta tal cual.

Uso:
    python exportar_proyecto.py
"""
from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "corpus-notebooklm"

# Se enmascara el dato, no la linea entera: asi el texto sigue leyendose igual
# y se ve que ahi habia un contacto.
PERSONALES = [
    # Telefono (formato MX +52) y CUALQUIER correo se enmascaran: no aportan a
    # las preguntas del cuaderno y no deben salir a un servicio externo.
    (re.compile(r"\+?52[\s-]?\d{2,3}[\s-]?\d{4}[\s-]?\d{4}"), "[telefono omitido]"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[correo omitido]"),
    # La CURP es el identificador con el que en Mexico se abre practicamente
    # cualquier tramite: no puede acabar en un documento que se comparte por
    # enlace. El patron es el formato oficial, no una CURP concreta.
    (re.compile(r"\b[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]{2}\b"), "[CURP omitida]"),
]

GRUPOS = [
    ("04-guia-del-sistema", "Guia de uso del sistema ULTRA CHAMBA",
     ["00-INICIO.md", "01-wiki.md", "estado-actual.md", "hoja-de-producto.md",
      "reglas-de-la-boveda.md", "guia-de-migracion.md", "plantilla-nota.md",
      "Obisidian rules.md", "guias/*.md"]),
    ("05-perfil-y-estrategia", "Perfil del candidato y estrategia de busqueda",
     ["perfil/*.md"]),
    ("06-arquitectura-y-decisiones", "Como esta construido el sistema y por que",
     ["sistema/*.md"]),
    ("07-codigo-fuente", "Codigo fuente completo", ["app/*.py"]),
    ("08-fichas-de-vacantes", "Fichas individuales de las vacantes destacadas",
     ["vacantes/*.md"]),
]


def _limpiar(texto: str) -> str:
    for patron, reemplazo in PERSONALES:
        texto = patron.sub(reemplazo, texto)
    return texto


def _recolectar(patrones: list[str]) -> list[Path]:
    vistos: list[Path] = []
    for patron in patrones:
        for ruta in sorted(RAIZ.glob(patron)):
            if ruta.is_file() and ruta not in vistos:
                vistos.append(ruta)
    return vistos


def exportar() -> dict:
    SALIDA.mkdir(exist_ok=True)
    resumen = {}

    for nombre, titulo, patrones in GRUPOS:
        archivos = _recolectar(patrones)
        if not archivos:
            continue

        partes = [
            f"{titulo.upper()}\n"
            f"Parte del proyecto ULTRA CHAMBA, un buscador de vacantes de "
            f"ciberseguridad e IA.\n"
            f"{len(archivos)} archivos. Cada bloque empieza con 'ARCHIVO:' y su "
            f"ruta real dentro del proyecto, para que cualquier respuesta pueda "
            f"rastrearse hasta el archivo concreto.\n"
            f"El telefono y el correo personales estan omitidos a proposito.\n"
        ]
        for ruta in archivos:
            rel = ruta.relative_to(RAIZ).as_posix()
            try:
                contenido = ruta.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                contenido = ruta.read_text(encoding="latin-1")
            partes.append(
                f"\n{'=' * 80}\nARCHIVO: {rel}\n{'-' * 80}\n{_limpiar(contenido)}\n")

        cuerpo = "".join(partes)
        destino = SALIDA / f"{nombre}.txt"
        destino.write_text(cuerpo, encoding="utf-8")
        resumen[nombre] = {"archivos": len(archivos), "palabras": len(cuerpo.split()),
                           "kb": round(len(cuerpo.encode("utf-8")) / 1024)}

    return resumen


def comprobar_fugas() -> list[str]:
    """Ultima red: busca datos personales en lo ya escrito."""
    fugas = []
    for txt in SALIDA.glob("*.txt"):
        contenido = txt.read_text(encoding="utf-8")
        for patron, _ in PERSONALES:
            if patron.search(contenido):
                fugas.append(f"{txt.name}: {patron.pattern}")
    return fugas


if __name__ == "__main__":
    res = exportar()
    print(f"corpus del proyecto en {SALIDA}")
    for nombre, r in res.items():
        print(f"  {nombre:30} {r['archivos']:4} archivos  "
              f"{r['palabras']:8,} palabras  {r['kb']:5} KB")

    fugas = comprobar_fugas()
    if fugas:
        print("\n!! SE ESCAPARON DATOS PERSONALES:")
        for f in fugas:
            print(f"   {f}")
        raise SystemExit(1)
    print("\ncomprobado: ningun telefono ni correo personal en la salida")

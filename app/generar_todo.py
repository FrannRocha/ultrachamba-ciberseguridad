"""
Punto de entrada unico: reconstruye el dashboard y la boveda Obsidian.

    python app/generar_todo.py

Asume que `pipeline.py` ya corrio y dejo los JSON en `app/datos/`.
Para el ciclo completo desde cero:

    python app/pipeline.py && python app/generar_todo.py
"""
from __future__ import annotations

import generar_dashboard
import generar_obsidian as go
import generar_obsidian_estrategia as ge
import generar_obsidian_guias as gg
import generar_obsidian_seguimiento as gs
import generar_obsidian_vault as gv
from nucleo import cargar_json, log


def refrescar_json_desde_base() -> int:
    """Reescribe `vacantes.json` con lo que dice la base AHORA MISMO.

    Por que existe. El dashboard y la boveda leian `vacantes.json`, mientras
    que el panel en vivo, el corpus y Drive leian la base. Eran dos fuentes de
    verdad sin declarar, y divergieron: el dashboard llego a mostrar 210
    vacantes que la base ya habia descartado (guardias de seguridad,
    practicantes de rentabilidad) y a ocultar otras 447 que si valian. Un
    reanalisis actualizaba la base y no tocaba el JSON, asi que el desfase
    podia ser indefinido.

    Ahora el JSON es un derivado que se regenera justo antes de usarlo, no una
    fuente paralela. La base manda siempre.
    """
    import json
    from almacen import SQL_VIVAS_EXPORTABLES, conexion
    from nucleo import DATOS

    with conexion() as con:
        # El filtro NO se escribe aqui: es `almacen.SQL_VIVAS_EXPORTABLES`, el
        # del panel mas `elegible_mx = 1`. Tenerlo copiado era como acabaron
        # cinco notas de la boveda publicando una cifra distinta de la del
        # panel el mismo dia (27-ago-2026).
        filas = con.execute(
            f"SELECT * FROM vacantes WHERE {SQL_VIVAS_EXPORTABLES} "
            "ORDER BY score DESC").fetchall()

    salida = []
    for f in filas:
        v = dict(f)
        for campo in ("motivos", "habilidades", "extra"):
            try:
                v[campo] = json.loads(v.get(campo) or ("[]" if campo != "extra" else "{}"))
            except (TypeError, ValueError):
                v[campo] = [] if campo != "extra" else {}
        v["habilidades_coincidentes"] = v.get("habilidades") or []
        v["elegible_mx"] = bool(v.get("elegible_mx"))
        v["requiere_mudanza"] = bool(v.get("requiere_mudanza"))
        v["aplicada"] = bool(v.get("aplicada"))
        v["verificacion"] = {
            "estado": v.pop("ver_estado", None), "metodo": v.pop("ver_metodo", None),
            "detalle": v.pop("ver_detalle", None), "fecha": v.pop("ver_fecha", None),
            "http": v.pop("ver_http", None),
        }
        salida.append(v)

    (DATOS / "vacantes.json").write_text(
        json.dumps(salida, ensure_ascii=False), encoding="utf-8")
    return len(salida)


def main() -> int:
    est = cargar_json("estadisticas.json", {})
    n = refrescar_json_desde_base()
    log(f"vacantes.json regenerado desde la base: {n} vacantes")
    vacantes = cargar_json("vacantes.json", [])
    if not vacantes:
        log("No hay datos. Ejecuta primero: python app/pipeline.py")
        return 1

    log("=" * 62)
    log("GENERANDO ENTREGABLES")
    log("=" * 62)

    log("\n[1/3] Dashboard")
    generar_dashboard.generar()

    log("\n[2/3] Boveda Obsidian")
    go._indice.clear()
    go.notas_sistema(est)
    go.notas_herramientas(est)
    go.notas_investigacion()
    go.notas_diseno()
    go.notas_perfil()
    # El giro de agosto: empresas, cola, correos en frio y formacion.
    ge.notas_estrategia(est)
    # El seguimiento: que pasa DESPUES de enviar. La nota de procesos en
    # marcha se genera desde la base, asi que se corrige sola en cada corrida.
    gs.notas_seguimiento(est)
    gg.notas_guias(est, vacantes)
    n = gv.notas_vacantes(vacantes)
    gv.notas_navegacion(est, vacantes)
    gv.escribir_wiki()

    log("\n[3/3] Verificacion de la boveda")
    gv.informe(n)

    log("\n" + "=" * 62)
    log("LISTO")
    log("  Panel:   dashboard.html  (doble clic)")
    log("  Boveda:  abrir esta carpeta en Obsidian, empezar por 00-INICIO.md")
    log("=" * 62)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

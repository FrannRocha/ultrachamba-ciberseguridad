"""
Correcciones y altas manuales al mapa de empresas (EJEMPLOS).

PLANTILLA. El mapa de `empresas.py` se construye desde las vacantes
recolectadas, y eso tiene dos puntos ciegos: (1) el volumen de anuncios no mide
la presencia local real de una empresa, y (2) las mejores puertas a veces no
publican vacantes. Este archivo permite corregir ambos a mano.

Las entradas de abajo son ficticias (score 0, dominio example.com) y solo
muestran la estructura. Sustituyelas por tus propias correcciones, con su
evidencia. No publiques datos personales de terceros aqui.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Altas manuales: objetivos que no publican vacantes en nuestras fuentes y por
# eso el mapa no los ve. `score` es manual porque no hay anuncios que contar;
# se anota el porque en `notas`.
# ---------------------------------------------------------------------------
MANUALES = [
    {
        "nombre": "EJEMPLO — Empresa de Ciberseguridad",
        "nombre_limpio": "EJEMPLO — Empresa de Ciberseguridad",
        "dominio": "example.com", "sitio": "https://example.com",
        "sector": "ciberseguridad", "en_monterrey": 0, "score": 0,
        "via": "espontanea",
        "notas": "EJEMPLO. Empresa que no publica en las fuentes y que quieres "
                 "tener en el mapa. Pon aqui tu evidencia; no incluyas datos "
                 "personales de terceros.",
        "motivos": ["EJEMPLO: por que es un buen objetivo"],
    },
]

# ---------------------------------------------------------------------------
# Ajustes a empresas que el mapa SI ve, pero mal. La clave casa contra el
# nombre normalizado; `factor` multiplica el score y `nota` explica por que,
# para que el ajuste sea auditable y no un numero magico.
# ---------------------------------------------------------------------------
AJUSTES = {
    "ejemplo-empresa": {
        "factor": 1.0,
        "nota": "EJEMPLO. Sube o baja el score de una empresa con su motivo "
                "(p. ej. su operacion real de TI esta en otra ciudad, o es "
                "100% remota sin oficina local).",
    },
}

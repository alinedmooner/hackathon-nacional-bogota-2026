"""Capa de servicio para las alertas Veridia.

Mismo patrón cache-aside que analytics_paso2_service.py.
Cache en colección 'radar_cache' (namespace separado de 'analytics_cache').
"""
from services import cache_service as cache
from repositories import radar_repo

_P = "radar_"  # prefijo de namespace en el cache


# ── Dashboard ─────────────────────────────────────────────────────────────────

def dashboard() -> dict:
    def compute():
        return radar_repo.resumen_global()
    return cache.cached(f"{_P}dashboard", compute)


# ── UC-01: Sancionados activos ────────────────────────────────────────────────

def sancionados_resumen() -> dict:
    def compute():
        return radar_repo.sancionados_activos_resumen()
    return cache.cached(f"{_P}sancionados_resumen", compute)


def sancionados_lista(limit: int, offset: int) -> dict:
    def compute():
        rows = radar_repo.sancionados_activos(limit=limit, offset=offset)
        return {"hallazgos": rows, "limit": limit, "offset": offset, "total_pagina": len(rows)}
    return cache.cached(f"{_P}sancionados_{limit}_{offset}", compute)


# ── UC-02: Multados activos ───────────────────────────────────────────────────

def multados_resumen() -> dict:
    def compute():
        return radar_repo.multados_activos_resumen()
    return cache.cached(f"{_P}multados_resumen", compute)


def multados_lista(limit: int, offset: int) -> dict:
    def compute():
        rows = radar_repo.multados_activos(limit=limit, offset=offset)
        return {"hallazgos": rows, "limit": limit, "offset": offset, "total_pagina": len(rows)}
    return cache.cached(f"{_P}multados_{limit}_{offset}", compute)


# ── UC-03: Puerta giratoria ───────────────────────────────────────────────────

def puerta_giratoria_resumen() -> dict:
    def compute():
        return radar_repo.puerta_giratoria_resumen()
    return cache.cached(f"{_P}puerta_resumen", compute)


def puerta_giratoria_lista(limit: int, offset: int) -> dict:
    def compute():
        rows = radar_repo.puerta_giratoria(limit=limit, offset=offset)
        return {"hallazgos": rows, "limit": limit, "offset": offset, "total_pagina": len(rows)}
    return cache.cached(f"{_P}puerta_{limit}_{offset}", compute)


# ── Grafo relacional ─────────────────────────────────────────────────────────

def grafo_entidad(nit: str, limit: int) -> dict:
    nit_norm = "".join(c for c in nit if c.isdigit())

    def compute():
        return radar_repo.grafo_entidad(nit=nit_norm, limit=limit)
    return cache.cached(f"{_P}grafo_{nit_norm}_{limit}", compute)


# ── UC-05: Perfil de documento ────────────────────────────────────────────────

def perfil(documento: str) -> dict:
    doc_norm = "".join(c for c in documento if c.isdigit())

    def compute():
        return radar_repo.perfil_documento(doc_norm)
    return cache.cached(f"{_P}perfil_{doc_norm}", compute)
